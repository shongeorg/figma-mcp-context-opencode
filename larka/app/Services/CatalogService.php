<?php

namespace App\Services;

use App\Models\Category;
use App\Models\Product;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Collection;
use Illuminate\Http\Request;
use Illuminate\Pagination\LengthAwarePaginator;

class CatalogService
{
    public const TABS = ['all', 'new', 'sale'];

    public const SORTS = ['default', 'price-asc', 'price-desc', 'name'];

    /**
     * @return array{
     *     products: LengthAwarePaginator,
     *     categories: Collection<int, Category>,
     *     tab: string,
     *     priceBounds: array{min: int, max: int},
     *     totalProducts: int,
     *     currentCategory: Category|null
     * }
     */
    public function data(Request $request, int $perPage = 9): array
    {
        $tab = $request->string('tab', 'all')->toString();
        $tab = in_array($tab, self::TABS, true) ? $tab : 'all';

        $sort = $request->string('sort', 'default')->toString();
        $sort = in_array($sort, self::SORTS, true) ? $sort : 'default';

        $bounds = Product::query()
            ->selectRaw('min(price) as min_price, max(price) as max_price')
            ->first();

        $categories = Category::withCount('products')->orderBy('position')->get();

        $currentCategory = null;

        $query = Product::with('images')->withCount('reviews');

        if ($request->filled('category')) {
            $currentCategory = Category::where('slug', $request->string('category')->toString())->first();

            if ($currentCategory !== null) {
                $query->whereIn('category_id', $currentCategory->descendantsIds());
            }
        }

        if ($tab === 'new') {
            $query->where('is_new', true);
        }

        if ($tab === 'sale') {
            $query->onSale();
        }

        if ($request->filled('q')) {
            $search = $request->string('q')->toString();
            $query->where(function (Builder $builder) use ($search) {
                $builder->where('name', 'ilike', "%{$search}%")
                    ->orWhere('short_description', 'ilike', "%{$search}%");
            });
        }

        if ($request->filled('min')) {
            $query->where('price', '>=', (float) $request->input('min'));
        }

        if ($request->filled('max')) {
            $query->where('price', '<=', (float) $request->input('max'));
        }

        if ($request->filled('size')) {
            $query->whereJsonContains('sizes', $request->string('size')->toString());
        }

        match ($sort) {
            'price-asc' => $query->orderBy('price'),
            'price-desc' => $query->orderByDesc('price'),
            'name' => $query->orderBy('name'),
            default => $query->orderByDesc('is_new')->orderByDesc('id'),
        };

        return [
            'products' => $query->paginate($perPage)->withQueryString(),
            'categories' => $categories,
            'tab' => $tab,
            'priceBounds' => [
                'min' => (int) floor($bounds->min_price ?? 0),
                'max' => (int) ceil($bounds->max_price ?? 999),
            ],
            'totalProducts' => Product::count(),
            'currentCategory' => $currentCategory,
        ];
    }
}
