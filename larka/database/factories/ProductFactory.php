<?php

namespace Database\Factories;

use App\Models\Category;
use App\Models\Product;
use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Str;

/**
 * @extends Factory<Product>
 */
class ProductFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        $name = Str::title(fake()->unique()->words(2, true));

        return [
            'category_id' => Category::factory(),
            'name' => $name,
            'slug' => Str::slug($name).'-'.uniqid(),
            'sku' => 'GS-'.fake()->unique()->numberBetween(1, 999999),
            'short_description' => fake()->sentence(10),
            'description' => fake()->paragraph(3),
            'price' => fake()->randomFloat(2, 15, 300),
            'old_price' => null,
            'discount_percent' => null,
            'rating' => fake()->randomFloat(2, 0, 5),
            'reviews_count' => fake()->numberBetween(0, 60),
            'stock' => fake()->numberBetween(5, 50),
            'is_new' => false,
            'sizes' => null,
            'sold_count' => fake()->numberBetween(0, 200),
        ];
    }

    /**
     * Indicate that the product is currently on sale.
     */
    public function onSale(): static
    {
        return $this->state(fn (array $attributes) => [
            'old_price' => round($attributes['price'] * 1.3, 2),
            'discount_percent' => 30,
        ]);
    }

    /**
     * Indicate that the product was just added to the catalogue.
     */
    public function isNew(): static
    {
        return $this->state(fn (array $attributes) => [
            'is_new' => true,
        ]);
    }

    /**
     * Indicate that the product is out of stock.
     */
    public function outOfStock(): static
    {
        return $this->state(fn (array $attributes) => [
            'stock' => 0,
        ]);
    }
}
