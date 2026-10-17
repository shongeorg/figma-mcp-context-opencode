<?php

namespace App\Services;

use App\Models\CartItem;
use App\Models\Product;
use Illuminate\Support\Collection;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Session;

class CartService
{
    /**
     * @return Collection<int, array{product: Product, size: string, quantity: int}>
     */
    public function lines(): Collection
    {
        if (Auth::check()) {
            return CartItem::with('product')
                ->where('user_id', Auth::id())
                ->get()
                ->map(fn (CartItem $item) => [
                    'product' => $item->product,
                    'size' => $item->size,
                    'quantity' => $item->quantity,
                ])
                ->filter(fn (array $line) => $line['product'] !== null)
                ->values();
        }

        $lines = [];

        foreach (Session::get('cart', []) as $key => $line) {
            $product = Product::with('images')->find($line['product_id']);

            if ($product !== null) {
                $lines[$key] = [
                    'product' => $product,
                    'size' => $line['size'] ?? '',
                    'quantity' => $line['quantity'],
                ];
            }
        }

        return collect($lines)->values();
    }

    public function add(int $productId, string $size = '', int $quantity = 1): void
    {
        $quantity = max(1, $quantity);

        if (Auth::check()) {
            $item = CartItem::firstOrCreate(
                ['user_id' => Auth::id(), 'product_id' => $productId, 'size' => $size],
                ['quantity' => 0],
            );

            $item->increment('quantity', $quantity);

            return;
        }

        $cart = Session::get('cart', []);
        $key = $productId.'|'.$size;
        $existing = $cart[$key]['quantity'] ?? 0;

        $cart[$key] = [
            'product_id' => $productId,
            'size' => $size,
            'quantity' => $existing + $quantity,
        ];

        Session::put('cart', $cart);
    }

    public function updateQuantity(int $productId, string $size, int $quantity): void
    {
        if (Auth::check()) {
            $query = CartItem::where('user_id', Auth::id())->where('product_id', $productId)->where('size', $size);

            if ($quantity <= 0) {
                $query->delete();

                return;
            }

            $query->update(['quantity' => $quantity]);

            return;
        }

        $cart = Session::get('cart', []);
        $key = $productId.'|'.$size;

        if (! isset($cart[$key])) {
            return;
        }

        if ($quantity <= 0) {
            unset($cart[$key]);
        } else {
            $cart[$key]['quantity'] = $quantity;
        }

        Session::put('cart', $cart);
    }

    public function remove(int $productId, string $size): void
    {
        $this->updateQuantity($productId, $size, 0);
    }

    public function clear(): void
    {
        if (Auth::check()) {
            CartItem::where('user_id', Auth::id())->delete();

            return;
        }

        Session::forget('cart');
    }

    public function count(): int
    {
        return (int) $this->lines()->sum(fn (array $line) => $line['quantity']);
    }

    public function subtotal(): float
    {
        return round($this->lines()->sum(fn (array $line) => $line['product']->price * $line['quantity']), 2);
    }

    public function mergeSessionToUser(int $userId): void
    {
        $cart = Session::get('cart', []);

        if ($cart === []) {
            return;
        }

        foreach ($cart as $line) {
            $item = CartItem::firstOrCreate(
                ['user_id' => $userId, 'product_id' => $line['product_id'], 'size' => $line['size'] ?? ''],
                ['quantity' => 0],
            );

            $item->increment('quantity', (int) $line['quantity']);
        }

        Session::forget('cart');
    }
}
