<?php

use App\Models\Category;
use App\Models\Product;
use App\Models\User;

test('the header cart badge reflects the signed in cart', function () {
    $user = User::factory()->create();
    $product = Product::factory()->create(['stock' => 10]);

    $this->actingAs($user)->post(route('cart.store'), [
        'product_id' => $product->id,
        'quantity' => 3,
    ]);

    $this->actingAs($user)
        ->get(route('home'))
        ->assertOk()
        ->assertSee('Cart, 3 items', false);
});

test('the footer lists every category', function () {
    Category::factory()->create(['name' => 'House Plants', 'slug' => 'house-plants', 'position' => 1]);
    Category::factory()->create(['name' => 'Plant Pots', 'slug' => 'plant-pots', 'position' => 2]);

    $this->get(route('home'))
        ->assertOk()
        ->assertSee('House Plants')
        ->assertSee('Plant Pots');
});
