<?php

namespace App\Models;

use Database\Factories\ProductFactory;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Collection;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

/**
 * @property int $id
 * @property int $category_id
 * @property string $name
 * @property string $slug
 * @property string $sku
 * @property string|null $short_description
 * @property string|null $description
 * @property float $price
 * @property float|null $old_price
 * @property int|null $discount_percent
 * @property float $rating
 * @property int $reviews_count
 * @property int $stock
 * @property bool $is_new
 * @property array<int, string>|null $sizes
 * @property int $sold_count
 * @property-read Category $category
 * @property-read Collection<int, ProductImage> $images
 */
class Product extends Model
{
    /** @use HasFactory<ProductFactory> */
    use HasFactory;

    protected $fillable = [
        'category_id', 'name', 'slug', 'sku', 'short_description', 'description',
        'price', 'old_price', 'discount_percent', 'rating', 'reviews_count',
        'stock', 'is_new', 'sizes', 'sold_count',
    ];

    protected function casts(): array
    {
        return [
            'price' => 'float',
            'old_price' => 'float',
            'discount_percent' => 'integer',
            'rating' => 'float',
            'is_new' => 'boolean',
            'sizes' => 'array',
        ];
    }

    public function category(): BelongsTo
    {
        return $this->belongsTo(Category::class);
    }

    /** @return HasMany<ProductImage> */
    public function images(): HasMany
    {
        return $this->hasMany(ProductImage::class)->orderBy('position');
    }

    /** @return HasMany<Review> */
    public function reviews(): HasMany
    {
        return $this->hasMany(Review::class)->latest();
    }

    public function scopeInStock(Builder $query): Builder
    {
        return $query->where('stock', '>', 0);
    }

    public function scopeOnSale(Builder $query): Builder
    {
        return $query->whereNotNull('old_price');
    }

    public function getDiscountPercentAttribute(): ?int
    {
        if ($this->attributes['discount_percent'] !== null) {
            return (int) $this->attributes['discount_percent'];
        }

        if ($this->old_price && $this->old_price > $this->price) {
            return (int) round((1 - $this->price / $this->old_price) * 100);
        }

        return null;
    }

    public function getMainImageAttribute(): ?string
    {
        return $this->images->first()?->path;
    }

    public function getIsSaleAttribute(): bool
    {
        return $this->old_price !== null && $this->old_price > $this->price;
    }
}
