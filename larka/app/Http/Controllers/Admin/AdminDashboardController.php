<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Models\Product;
use App\Models\User;
use Illuminate\Contracts\View\View;

class AdminDashboardController extends Controller
{
    public function __invoke(): View
    {
        return view('admin.dashboard', [
            'productCount' => Product::count(),
            'orderCount' => Order::count(),
            'userCount' => User::where('role', 'user')->count(),
            'revenue' => (float) Order::where('status', '!=', Order::STATUS_CANCELLED)->sum('total'),
            'recentOrders' => Order::with('user')->latest('placed_at')->take(8)->get(),
        ]);
    }
}
