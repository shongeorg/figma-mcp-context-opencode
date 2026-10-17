<?php

namespace App\Services\ImageSearch;

class PexelsImageProvider extends BaseImageProvider
{
    protected function endpoint(): string
    {
        return 'https://api.pexels.com/v1/search';
    }

    protected function apiKey(): string
    {
        return (string) config('services.pexels.key');
    }

    /**
     * @param  array<string, mixed>  $payload
     * @return array<int, string>
     */
    protected function extractUrls(array $payload): array
    {
        $photos = $payload['photos'] ?? [];

        return collect($photos)
            ->map(fn (array $photo) => $photo['src']['large2x'] ?? $photo['src']['large'] ?? null)
            ->filter()
            ->values()
            ->all();
    }

    protected function authHeaders(): array
    {
        return ['Authorization' => $this->apiKey()];
    }
}
