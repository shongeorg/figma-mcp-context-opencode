<?php

namespace Database\Seeders;

use App\Models\Category;
use Illuminate\Database\Seeder;
use Illuminate\Support\Str;

class CategorySeeder extends Seeder
{
    /** @var array<int, string> */
    private const NAMES = [
        'House Plants',
        'Potter Plants',
        'Seeds',
        'Small Plants',
        'Big Plants',
        'Succulents',
        'Terrariums',
        'Gardening',
        'Accessories',
    ];

    public function run(): void
    {
        foreach (self::NAMES as $position => $name) {
            Category::updateOrCreate(
                ['slug' => Str::slug($name)],
                [
                    'name' => $name,
                    'position' => $position,
                ],
            );
        }
    }
}
