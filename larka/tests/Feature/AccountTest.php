<?php

use App\Models\User;

test('account page is displayed', function () {
    $user = User::factory()->create();

    $response = $this
        ->actingAs($user)
        ->get(route('account.show'));

    $response->assertOk();
});

test('guests are redirected to the login page from the account', function () {
    $response = $this->get(route('account.show'));

    $response->assertRedirect(route('login'));
});

test('profile information can be updated', function () {
    $user = User::factory()->create();

    $response = $this
        ->actingAs($user)
        ->from(route('account.show'))
        ->put(route('account.update'), [
            'name' => 'Test User',
            'email' => 'test@example.com',
        ]);

    $response
        ->assertSessionHasNoErrors()
        ->assertRedirect(route('account.show'));

    $user->refresh();

    expect($user->name)->toBe('Test User');
    expect($user->email)->toBe('test@example.com');
});

test('profile update rejects an email already taken by another user', function () {
    $user = User::factory()->create();
    $taken = User::factory()->create(['email' => 'taken@example.com']);

    $response = $this
        ->actingAs($user)
        ->put(route('account.update'), [
            'name' => 'Test User',
            'email' => $taken->email,
        ]);

    $response->assertSessionHasErrors('email');

    expect($user->refresh()->email)->not->toBe($taken->email);
});

test('orders page lists the orders of the signed in user only', function () {
    $user = User::factory()->create();
    $own = $user->orders()->create([
        'number' => 'GS-261017-AAAA',
        'status' => 'pending',
        'shipping_address' => ['city' => 'Farmingdale'],
        'total' => 129,
    ]);

    $other = User::factory()->create()->orders()->create([
        'number' => 'GS-261017-BBBB',
        'status' => 'pending',
        'shipping_address' => ['city' => 'Nowhere'],
        'total' => 500,
    ]);

    $response = $this
        ->actingAs($user)
        ->get(route('account.orders'));

    $response
        ->assertOk()
        ->assertSee($own->number)
        ->assertDontSee($other->number);
});
