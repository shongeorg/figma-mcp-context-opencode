<?php

use App\Models\User;
use Illuminate\Support\Facades\Hash;

test('password can be changed from the account page', function () {
    $user = User::factory()->create();

    $response = $this
        ->actingAs($user)
        ->from(route('account.show'))
        ->put(route('account.password'), [
            'current_password' => 'password',
            'password' => 'new-password',
            'password_confirmation' => 'new-password',
        ]);

    $response
        ->assertSessionHasNoErrors()
        ->assertRedirect(route('account.show'));

    expect(Hash::check('new-password', $user->refresh()->password))->toBeTrue();
});

test('correct password must be provided to change the password', function () {
    $user = User::factory()->create();

    $response = $this
        ->actingAs($user)
        ->put(route('account.password'), [
            'current_password' => 'wrong-password',
            'password' => 'new-password',
            'password_confirmation' => 'new-password',
        ]);

    $response->assertSessionHasErrors('current_password');

    expect(Hash::check('password', $user->refresh()->password))->toBeTrue();
});

test('password confirmation must match when changing the password', function () {
    $user = User::factory()->create();

    $response = $this
        ->actingAs($user)
        ->put(route('account.password'), [
            'current_password' => 'password',
            'password' => 'new-password',
            'password_confirmation' => 'different',
        ]);

    $response->assertSessionHasErrors('password');

    expect(Hash::check('password', $user->refresh()->password))->toBeTrue();
});
