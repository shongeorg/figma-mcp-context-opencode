<?php

namespace App\Http\Controllers;

use App\Models\Coupon;
use App\Models\Order;
use App\Models\OrderItem;
use App\Models\Product;
use App\Services\CartService;
use Illuminate\Contracts\View\View;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\DB;

class CheckoutController extends Controller
{
    public function __construct(private readonly CartService $cart) {}

    public function show(): View
    {
        $lines = $this->cart->lines();

        if ($lines->isEmpty()) {
            return redirect()->route('cart.index');
        }

        $subtotal = round($lines->sum(fn (array $line) => $line['product']->price * $line['quantity']), 2);

        $coupon = session('coupon');
        $discount = 0.0;

        if ($coupon !== null) {
            $discount = $coupon['type'] === 'percent'
                ? round($subtotal * $coupon['value'] / 100, 2)
                : min((float) $coupon['value'], $subtotal);
        }

        $shipping = 16.0;

        return view('checkout.show', [
            'lines' => $lines,
            'subtotal' => $subtotal,
            'discount' => $discount,
            'shipping' => $shipping,
            'total' => round($subtotal - $discount + $shipping, 2),
            'addresses' => Auth::check() ? Auth::user()->addresses()->get() : collect(),
            'user' => Auth::user(),
        ]);
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'first_name' => ['required', 'string', 'max:100'],
            'last_name' => ['required', 'string', 'max:100'],
            'street' => ['required', 'string', 'max:255'],
            'city' => ['required', 'string', 'max:100'],
            'region' => ['nullable', 'string', 'max:100'],
            'postal_code' => ['nullable', 'string', 'max:16'],
            'phone' => ['required', 'string', 'max:32'],
            'email' => ['required', 'email', 'max:255'],
            'payment_method' => ['required', 'in:cod,card,bank'],
            'note' => ['nullable', 'string', 'max:1000'],
        ]);

        $lines = $this->cart->lines();

        if ($lines->isEmpty()) {
            return redirect()->route('cart.index');
        }

        $subtotal = round($lines->sum(fn (array $line) => $line['product']->price * $line['quantity']), 2);

        $couponModel = null;
        $couponCode = null;
        $discount = 0.0;

        if (session()->has('coupon')) {
            $coupon = session('coupon');
            $couponModel = Coupon::where('code', $coupon['code'])->first();

            if ($couponModel !== null && $couponModel->isValidFor($subtotal)) {
                $couponCode = $couponModel->code;
                $discount = $couponModel->discountFor($subtotal);
            }
        }

        $shipping = 16.0;
        $total = round($subtotal - $discount + $shipping, 2);

        $order = DB::transaction(function () use ($validated, $lines, $subtotal, $discount, $shipping, $total, $couponModel, $couponCode) {
            $order = Order::create([
                'user_id' => Auth::id(),
                'number' => Order::generateNumber(),
                'status' => Order::STATUS_PENDING,
                'payment_method' => $validated['payment_method'],
                'subtotal' => $subtotal,
                'discount' => $discount,
                'shipping' => $shipping,
                'total' => $total,
                'coupon_code' => $couponCode,
                'shipping_address' => [
                    'first_name' => $validated['first_name'],
                    'last_name' => $validated['last_name'],
                    'street' => $validated['street'],
                    'city' => $validated['city'],
                    'region' => $validated['region'] ?? null,
                    'postal_code' => $validated['postal_code'] ?? null,
                    'phone' => $validated['phone'],
                    'email' => $validated['email'],
                ],
                'note' => $validated['note'] ?? null,
                'placed_at' => now(),
            ]);

            foreach ($lines as $line) {
                OrderItem::create([
                    'order_id' => $order->id,
                    'product_id' => $line['product']->id,
                    'product_name' => $line['product']->name,
                    'product_sku' => $line['product']->sku,
                    'size' => $line['size'],
                    'image_path' => $line['product']->main_image,
                    'unit_price' => $line['product']->price,
                    'unit_old_price' => $line['product']->old_price,
                    'quantity' => $line['quantity'],
                    'line_total' => round($line['product']->price * $line['quantity'], 2),
                ]);

                Product::whereKey($line['product']->id)->decrement('stock', $line['quantity']);
                Product::whereKey($line['product']->id)->increment('sold_count', $line['quantity']);
            }

            if ($couponModel !== null) {
                $couponModel->increment('used_count');
            }

            return $order;
        });

        $this->cart->clear();
        session()->forget('coupon');

        return redirect()->route('orders.show', $order)->with('status', 'Your order has been placed.');
    }
}
