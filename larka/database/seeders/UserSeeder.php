<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;

class UserSeeder extends Seeder
{
    public function run(): void
    {
        User::updateOrCreate(
            ['email' => 'admin@admin.test'],
            [
                'name' => 'Admin',
                'password' => 'admin',
                'role' => 'admin',
                'balance' => 0,
                'email_verified_at' => now(),
            ],
        );

        User::updateOrCreate(
            ['email' => 'user@user.test'],
            [
                'name' => 'Demo User',
                'password' => 'user',
                'role' => 'user',
                'balance' => 250,
                'email_verified_at' => now(),
            ],
        );
    }
}
