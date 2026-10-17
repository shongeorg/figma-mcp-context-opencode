<?php

namespace App\Services\ImageSearch;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

abstract class BaseImageProvider implements ImageProvider
{
    /**
     * @return array<int, string>
     */
    public function search(string $query, int $count = 3): array
    {
        if ($this->apiKey() === '') {
            return [];
        }

        try {
            $response = Http::withHeaders($this->authHeaders())
                ->timeout(20)
                ->get($this->endpoint(), [
                    'query' => $query,
                    'per_page' => max(1, $count),
                ]);

            if (! $response->ok()) {
                Log::warning('Image provider responded with an error.', [
                    'provider' => static::class,
                    'status' => $response->status(),
                ]);

                return [];
            }

            return array_slice($this->extractUrls($response->json([])), 0, $count);
        } catch (\Throwable $exception) {
            Log::warning('Image provider request failed.', [
                'provider' => static::class,
                'error' => $exception->getMessage(),
            ]);

            return [];
        }
    }

    abstract protected function endpoint(): string;

    abstract protected function apiKey(): string;

    /**
     * @param  array<string, mixed>  $payload
     * @return array<int, string>
     */
    abstract protected function extractUrls(array $payload): array;

    /**
     * @return array<string, string>
     */
    protected function authHeaders(): array
    {
        return [];
    }
}
