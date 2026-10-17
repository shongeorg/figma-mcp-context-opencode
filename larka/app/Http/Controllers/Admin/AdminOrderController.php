<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Order;
use Illuminate\Contracts\View\View;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class AdminOrderController extends Controller
{
    public function index(Request $request): View
    {
        $query = Order::with(['user', 'items'])->latest('placed_at');

        if ($request->filled('status') && in_array($request->input('status'), Order::STATUSES, true)) {
            $query->where('status', $request->input('status'));
        }

        return view('admin.orders.index', [
            'orders' => $query->paginate(20)->withQueryString(),
            'statuses' => Order::STATUSES,
            'current' => $request->input('status'),
        ]);
    }

    public function updateStatus(Request $request, Order $order): RedirectResponse
    {
        $validated = $request->validate([
            'status' => ['required', 'in:'.implode(',', Order::STATUSES)],
        ]);

        $order->update(['status' => $validated['status']]);

        return back()->with('status', 'Order '.$order->number.' is now '.$validated['status'].'.');
    }

    public function destroy(Order $order): RedirectResponse
    {
        if ($order->is_paid) {
            return back()->with('error', 'Order '.$order->number.' has already shipped and cannot be deleted.');
        }

        $order->delete();

        return redirect()->route('admin.orders.index')->with('status', 'Order '.$order->number.' deleted.');
    }
}
