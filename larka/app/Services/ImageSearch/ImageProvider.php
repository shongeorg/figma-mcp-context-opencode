<?php

namespace App\Services\ImageSearch;

interface ImageProvider
{
    /**
     * @return array<int, string>
     */
    public function search(string $query, int $count = 3): array;
}
