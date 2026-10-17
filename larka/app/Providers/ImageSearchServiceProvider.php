<?php

namespace App\Providers;

use App\Services\ImageSearch\ImageProvider;
use App\Services\ImageSearch\PexelsImageProvider;
use App\Services\ImageSearch\PixabayImageProvider;
use App\Services\ImageSearch\ProductImageFetcher;
use App\Services\ImageSearch\UnsplashImageProvider;
use Illuminate\Support\ServiceProvider;

class ImageSearchServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->singleton(ProductImageFetcher::class, function () {
            /** @var array<int, class-string<ImageProvider>> $providers */
            $providers = [
                UnsplashImageProvider::class,
                PexelsImageProvider::class,
                PixabayImageProvider::class,
            ];

            return new ProductImageFetcher(
                array_map(fn (string $provider) => new $provider, $providers),
            );
        });
    }
}
