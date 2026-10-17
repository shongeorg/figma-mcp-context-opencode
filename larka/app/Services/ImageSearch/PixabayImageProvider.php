<?php

namespace App\Services\ImageSearch;

class PixabayImageProvider extends BaseImageProvider
{
    protected function endpoint(): string
    {
        return 'https://pixabay.com/api/';
    }

    protected function apiKey(): string
    {
        return (string) config('services.pixabay.key');
    }

    /**
     * @param  array<string, mixed>  $payload
     * @return array<int, string>
     */
    protected function extractUrls(array $payload): array
    {
        $hits = $payload['hits'] ?? [];

        return collect($hits)
            ->map(fn (array $hit) => $hit['largeImageURL'] ?? $hit['webformatURL'] ?? null)
            ->filter()
            ->values()
            ->all();
    }

    protected function authHeaders(): array
    {
        return [];
    }
}
