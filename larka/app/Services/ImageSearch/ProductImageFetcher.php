<?php

namespace App\Services\ImageSearch;

use App\Models\Product;
use App\Models\ProductImage;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;

class ProductImageFetcher
{
    /** @var array<int, ImageProvider> */
    private array $providers;

    /**
     * @param  array<int, ImageProvider>  $providers
     */
    public function __construct(array $providers)
    {
        $this->providers = $providers;
    }

    /**
     * @return array<int, string>
     */
    public function search(string $query, int $count = 3): array
    {
        foreach ($this->providers as $provider) {
            $urls = $provider->search($query, $count);

            if ($urls !== []) {
                return $urls;
            }
        }

        return [];
    }

    public function attachToProduct(Product $product, string $query, int $count = 3): int
    {
        $existing = $product->images()->count();

        if ($existing >= $count) {
            return 0;
        }

        $urls = $this->search($query, $count - $existing);

        $saved = 0;

        foreach ($urls as $index => $url) {
            $path = $this->download($product, $url, $existing + $index);

            if ($path === null) {
                continue;
            }

            ProductImage::create([
                'product_id' => $product->id,
                'path' => $path,
                'position' => $existing + $index,
            ]);

            $saved++;
        }

        return $saved;
    }

    private function download(Product $product, string $url, int $index): ?string
    {
        try {
            $response = Http::timeout(30)->get($url);

            if (! $response->ok()) {
                return null;
            }

            $extension = $this->extensionFrom($response->header('Content-Type'), $url);
            $directory = 'products/'.$product->slug;
            $filename = Str::slug($product->name).'-'.$index.'.'.$extension;

            Storage::disk('public')->put($directory.'/'.$filename, $response->body());

            return $directory.'/'.$filename;
        } catch (\Throwable $exception) {
            Log::warning('Failed to download a product image.', [
                'product' => $product->slug,
                'url' => $url,
                'error' => $exception->getMessage(),
            ]);

            return null;
        }
    }

    private function extensionFrom(string $contentType, string $url): string
    {
        $map = [
            'image/jpeg' => 'jpg',
            'image/png' => 'png',
            'image/webp' => 'webp',
            'image/gif' => 'gif',
        ];

        $type = strtolower(trim(Str::before($contentType, ';')));

        if (isset($map[$type])) {
            return $map[$type];
        }

        $extension = strtolower(pathinfo(parse_url($url, PHP_URL_PATH) ?? '', PATHINFO_EXTENSION));

        return in_array($extension, ['jpg', 'jpeg', 'png', 'webp', 'gif'], true) ? $extension : 'jpg';
    }
}
