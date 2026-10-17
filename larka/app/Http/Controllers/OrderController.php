<?php

namespace App\Http\Controllers;

use App\Models\Order;
use Illuminate\Contracts\View\View;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class OrderController extends Controller
{
    public function show(Request $request, int $order): View
    {
        $model = Auth::user()->orders()->with('items')->findOrFail($order);

        return view('orders.show', [
            'order' => $model,
        ]);
    }

    public function cancel(int $order): RedirectResponse
    {
        $model = Auth::user()->orders()->findOrFail($order);

        if (! $model->is_cancellable) {
            return back()->with('error', 'Order '.$model->number.' can no longer be cancelled.');
        }

        $model->update(['status' => Order::STATUS_CANCELLED]);

        return back()->with('status', 'Order '.$model->number.' has been cancelled.');
    }
}
