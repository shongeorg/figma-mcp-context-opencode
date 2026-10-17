<?php

use App\Models\Order;
use App\Models\User;

test('a customer can cancel a pending order', function () {
    $user = User::factory()->create();
    $order = $user->orders()->create([
        'number' => 'GS-261017-CANC',
        'status' => Order::STATUS_PENDING,
        'shipping_address' => ['city' => 'Farmingdale'],
        'total' => 129,
    ]);

    $response = $this
        ->actingAs($user)
        ->from(route('account.orders'))
        ->delete(route('orders.cancel', $order));

    $response
        ->assertSessionHasNoErrors()
        ->assertRedirect(route('account.orders'));

    expect($order->refresh()->status)->toBe(Order::STATUS_CANCELLED);
});

test('a shipped order cannot be cancelled', function () {
    $user = User::factory()->create();
    $order = $user->orders()->create([
        'number' => 'GS-261017-SHIP',
        'status' => Order::STATUS_SHIPPED,
        'shipping_address' => ['city' => 'Farmingdale'],
        'total' => 129,
    ]);

    $response = $this
        ->actingAs($user)
        ->from(route('account.orders'))
        ->delete(route('orders.cancel', $order));

    $response
        ->assertSessionHas('error')
        ->assertRedirect(route('account.orders'));

    expect($order->refresh()->status)->toBe(Order::STATUS_SHIPPED);
});

test('a customer cannot cancel the order of another user', function () {
    $owner = User::factory()->create();
    $order = $owner->orders()->create([
        'number' => 'GS-261017-OTHR',
        'status' => Order::STATUS_PENDING,
        'shipping_address' => ['city' => 'Nowhere'],
        'total' => 129,
    ]);

    $stranger = User::factory()->create();

    $this
        ->actingAs($stranger)
        ->delete(route('orders.cancel', $order))
        ->assertNotFound();

    expect($order->refresh()->status)->toBe(Order::STATUS_PENDING);
});

test('an admin can delete a pending order', function () {
    $admin = User::factory()->admin()->create();
    $customer = User::factory()->create();
    $order = $customer->orders()->create([
        'number' => 'GS-261017-DELE',
        'status' => Order::STATUS_PENDING,
        'shipping_address' => ['city' => 'Farmingdale'],
        'total' => 129,
    ]);

    $response = $this
        ->actingAs($admin)
        ->from(route('admin.orders.index'))
        ->delete(route('admin.orders.destroy', $order));

    $response
        ->assertSessionHasNoErrors()
        ->assertRedirect(route('admin.orders.index'));

    expect(Order::query()->find($order->id))->toBeNull();
});

test('an admin cannot delete an order that already shipped', function () {
    $admin = User::factory()->admin()->create();
    $customer = User::factory()->create();
    $order = $customer->orders()->create([
        'number' => 'GS-261017-PAID',
        'status' => Order::STATUS_DELIVERED,
        'shipping_address' => ['city' => 'Farmingdale'],
        'total' => 129,
    ]);

    $response = $this
        ->actingAs($admin)
        ->from(route('admin.orders.index'))
        ->delete(route('admin.orders.destroy', $order));

    $response
        ->assertSessionHas('error')
        ->assertRedirect(route('admin.orders.index'));

    expect(Order::query()->find($order->id))->not->toBeNull();
});

test('a non admin cannot delete an order', function () {
    $user = User::factory()->create();
    $customer = User::factory()->create();
    $order = $customer->orders()->create([
        'number' => 'GS-261017-FORB',
        'status' => Order::STATUS_PENDING,
        'shipping_address' => ['city' => 'Farmingdale'],
        'total' => 129,
    ]);

    $this
        ->actingAs($user)
        ->delete(route('admin.orders.destroy', $order))
        ->assertForbidden();

    expect(Order::query()->find($order->id))->not->toBeNull();
});
