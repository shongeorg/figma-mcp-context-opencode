<?php

namespace App\Services\ImageSearch;

class UnsplashImageProvider extends BaseImageProvider
{
    protected function endpoint(): string
    {
        return 'https://api.unsplash.com/search/photos';
    }

    protected function apiKey(): string
    {
        return (string) config('services.unsplash.key');
    }

    /**
     * @param  array<string, mixed>  $payload
     * @return array<int, string>
     */
    protected function extractUrls(array $payload): array
    {
        $results = $payload['results'] ?? [];

        return collect($results)
            ->map(fn (array $photo) => $photo['urls']['regular'] ?? null)
            ->filter()
            ->values()
            ->all();
    }

    protected function authHeaders(): array
    {
        return ['Authorization' => 'Client-ID '.$this->apiKey()];
    }
}
