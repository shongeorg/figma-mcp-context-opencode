<?php

use App\Models\User;

test('guests can browse the storefront', function () {
    $response = $this->get(route('home'));

    $response->assertOk();
});

test('authenticated users can browse the storefront', function () {
    $user = User::factory()->create();
    $this->actingAs($user);

    $response = $this->get(route('home'));

    $response->assertOk();
});

test('guests are redirected to the login page from the account', function () {
    $response = $this->get(route('account.show'));

    $response->assertRedirect(route('login'));
});
