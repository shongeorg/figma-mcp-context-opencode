<?php

namespace App\Http\Controllers;

use App\Models\Coupon;
use App\Models\Product;
use App\Services\CartService;
use Illuminate\Contracts\View\View;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class CartController extends Controller
{
    public function __construct(private readonly CartService $cart) {}

    public function index(): View
    {
        $lines = $this->cart->lines();

        $subtotal = round($lines->sum(fn (array $line) => $line['product']->price * $line['quantity']), 2);

        $coupon = session('coupon');

        $discount = 0.0;

        if ($coupon !== null && $subtotal > 0) {
            $discount = $coupon['type'] === 'percent'
                ? round($subtotal * $coupon['value'] / 100, 2)
                : min((float) $coupon['value'], $subtotal);
        }

        $shipping = $subtotal > 0 ? 16.0 : 0.0;

        $related = Product::with('images')->inStock()->latest('sold_count')->take(5)->get();

        return view('cart.index', [
            'lines' => $lines,
            'subtotal' => $subtotal,
            'discount' => $discount,
            'shipping' => $shipping,
            'total' => round($subtotal - $discount + $shipping, 2),
            'coupon' => $coupon,
            'related' => $related,
        ]);
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'product_id' => ['required', 'exists:products,id'],
            'size' => ['nullable', 'string', 'max:16'],
            'quantity' => ['nullable', 'integer', 'min:1', 'max:999'],
        ]);

        $product = Product::findOrFail($validated['product_id']);

        $this->cart->add(
            $product->id,
            (string) ($validated['size'] ?? ''),
            (int) ($validated['quantity'] ?? 1),
        );

        if ($request->boolean('redirect')) {
            return redirect()->route('cart.index')->with('status', $product->name.' added to your cart.');
        }

        return back()->with('status', $product->name.' added to your cart.');
    }

    public function update(Request $request)
    {
        $validated = $request->validate([
            'product_id' => ['required', 'integer'],
            'size' => ['nullable', 'string', 'max:16'],
            'quantity' => ['required', 'integer', 'min:0', 'max:999'],
        ]);

        $this->cart->updateQuantity(
            (int) $validated['product_id'],
            (string) ($validated['size'] ?? ''),
            (int) $validated['quantity'],
        );

        return back()->with('status', 'Cart updated.');
    }

    public function destroy(Request $request)
    {
        $validated = $request->validate([
            'product_id' => ['required', 'integer'],
            'size' => ['nullable', 'string', 'max:16'],
        ]);

        $this->cart->remove((int) $validated['product_id'], (string) ($validated['size'] ?? ''));

        return back()->with('status', 'Item removed from your cart.');
    }

    public function applyCoupon(Request $request)
    {
        $validated = $request->validate([
            'coupon' => ['required', 'string', 'max:32'],
        ]);

        $coupon = Coupon::where('code', $validated['coupon'])->first();
        $subtotal = $this->cart->subtotal();

        if ($coupon === null || ! $coupon->isValidFor($subtotal)) {
            return back()->withErrors(['coupon' => 'This coupon is not valid for your order.']);
        }

        session()->put('coupon', [
            'code' => $coupon->code,
            'type' => $coupon->type,
            'value' => (float) $coupon->value,
        ]);

        return back()->with('status', 'Coupon '.$coupon->code.' applied.');
    }

    public function removeCoupon(): RedirectResponse
    {
        session()->forget('coupon');

        return back()->with('status', 'Coupon removed.');
    }
}
