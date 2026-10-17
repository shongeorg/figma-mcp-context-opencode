<?php

namespace Database\Seeders;

use App\Models\Category;
use App\Models\Coupon;
use App\Models\Product;
use App\Services\ImageSearch\ProductImageFetcher;
use Illuminate\Database\Seeder;
use Illuminate\Support\Str;

class ProductSeeder extends Seeder
{
    /**
     * @var array<int, array{name: string, category: string, price: float, old_price: float|null, rating: float, stock: int, is_new: bool, sizes: array<int, string>, description: string}>
     */
    private const PRODUCTS = [
        ['name' => 'Barberton Daisy', 'category' => 'House Plants', 'price' => 119, 'old_price' => null, 'rating' => 4.8, 'stock' => 42, 'is_new' => false, 'sizes' => ['Small', 'Medium', 'Large'], 'description' => 'A tender perennial from South Africa that forms a rosette of toothed, blue-green leaves and throws up tall stems of large, daisy-like flowers from late winter.'],
        ['name' => 'Angel Wing Begonia', 'category' => 'House Plants', 'price' => 169, 'old_price' => null, 'rating' => 4.6, 'stock' => 28, 'is_new' => true, 'sizes' => ['Small', 'Medium'], 'description' => 'Spotted silver foliage shaped like angel wings, topped with sprays of coral flowers through the warmer months.'],
        ['name' => 'African Violet', 'category' => 'House Plants', 'price' => 199, 'old_price' => 229, 'rating' => 4.9, 'stock' => 15, 'is_new' => false, 'sizes' => ['Small'], 'description' => 'A compact bloomer that flowers almost continuously on a bright windowsill with steady warmth.'],
        ['name' => 'Beach Spider Lily', 'category' => 'House Plants', 'price' => 129, 'old_price' => null, 'rating' => 4.4, 'stock' => 33, 'is_new' => false, 'sizes' => ['Medium', 'Large'], 'description' => 'Strappy evergreen leaves and fragrant white spider flowers that bloom in late summer.'],
        ['name' => 'Blushing Bromeliad', 'category' => 'Potter Plants', 'price' => 139, 'old_price' => 159, 'rating' => 4.7, 'stock' => 21, 'is_new' => false, 'sizes' => ['Small', 'Medium'], 'description' => 'A rosette of glossy leaves with a blazing pink centre bract that lasts for months.'],
        ['name' => 'Aluminum Plant', 'category' => 'Small Plants', 'price' => 179, 'old_price' => null, 'rating' => 4.5, 'stock' => 40, 'is_new' => true, 'sizes' => ['Small', 'Medium'], 'description' => 'Pilea cadierei with silver-marked leaves that look stamped in aluminum, easy and compact.'],
        ['name' => "Bird's Nest Fern", 'category' => 'House Plants', 'price' => 99, 'old_price' => 129, 'rating' => 4.3, 'stock' => 55, 'is_new' => false, 'sizes' => ['Medium', 'Large'], 'description' => 'Bright apple-green fronds unfurling from a central rosette, happy in humid bathrooms.'],
        ['name' => 'Chinese Evergreen', 'category' => 'House Plants', 'price' => 39, 'old_price' => null, 'rating' => 4.2, 'stock' => 90, 'is_new' => false, 'sizes' => ['Small', 'Medium', 'Large'], 'description' => 'One of the most tolerant houseplants you can grow, with marbled silver and green foliage.'],
        ['name' => 'Broadleaf Lady Palm', 'category' => 'Big Plants', 'price' => 249, 'old_price' => 299, 'rating' => 4.9, 'stock' => 12, 'is_new' => false, 'sizes' => ['Large'], 'description' => 'A stately palm with fan-shaped divided leaves, excellent as a floor specimen.'],
        ['name' => 'Red Aglaonema', 'category' => 'House Plants', 'price' => 149, 'old_price' => null, 'rating' => 4.7, 'stock' => 26, 'is_new' => true, 'sizes' => ['Small', 'Medium'], 'description' => 'Deep green leaves flushed with scarlet, one of the easiest red foliage plants to keep.'],
        ['name' => 'Snake Plant Laurentii', 'category' => 'Small Plants', 'price' => 89, 'old_price' => 109, 'rating' => 4.8, 'stock' => 64, 'is_new' => false, 'sizes' => ['Small', 'Medium', 'Large'], 'description' => 'Upright banded foliage that tolerates neglect and filters indoor air overnight.'],
        ['name' => 'ZZ Plant', 'category' => 'House Plants', 'price' => 115, 'old_price' => null, 'rating' => 4.9, 'stock' => 48, 'is_new' => false, 'sizes' => ['Medium', 'Large'], 'description' => 'Glossy waxy leaves on arching stems, thriving on neglect and low light alike.'],
        ['name' => 'Fiddle Leaf Fig', 'category' => 'Big Plants', 'price' => 289, 'old_price' => 349, 'rating' => 4.1, 'stock' => 9, 'is_new' => false, 'sizes' => ['Large'], 'description' => 'The interior-design favourite with big violin-shaped leaves and a tree form.'],
        ['name' => 'Monstera Deliciosa', 'category' => 'Big Plants', 'price' => 259, 'old_price' => null, 'rating' => 4.9, 'stock' => 18, 'is_new' => true, 'sizes' => ['Large'], 'description' => 'Swiss cheese plant with fenestrated leaves that get more dramatic with age.'],
        ['name' => 'Peace Lily', 'category' => 'House Plants', 'price' => 79, 'old_price' => 99, 'rating' => 4.6, 'stock' => 70, 'is_new' => false, 'sizes' => ['Small', 'Medium'], 'description' => 'White spathes above deep green leaves; tells you clearly when it needs water.'],
        ['name' => 'Aloe Vera', 'category' => 'Succulents', 'price' => 45, 'old_price' => null, 'rating' => 4.7, 'stock' => 120, 'is_new' => false, 'sizes' => ['Small'], 'description' => 'The classic healing succulent, storing water in its toothed blue-green leaves.'],
        ['name' => 'Echeveria Lola', 'category' => 'Succulents', 'price' => 35, 'old_price' => 45, 'rating' => 4.5, 'stock' => 85, 'is_new' => false, 'sizes' => ['Small'], 'description' => 'A pale lavender rosette with a powdered finish, perfect for bright shelves.'],
        ['name' => 'Zebra Haworthia', 'category' => 'Succulents', 'price' => 29, 'old_price' => null, 'rating' => 4.4, 'stock' => 95, 'is_new' => true, 'sizes' => ['Small'], 'description' => 'Striped white bands on dark green pointed leaves, slow and sculptural.'],
        ['name' => 'Jade Plant', 'category' => 'Succulents', 'price' => 65, 'old_price' => 85, 'rating' => 4.8, 'stock' => 44, 'is_new' => false, 'sizes' => ['Small', 'Medium'], 'description' => 'A woody-stemmed succulent believed to bring prosperity, living for decades.'],
        ['name' => 'Christmas Cactus', 'category' => 'Succulents', 'price' => 55, 'old_price' => null, 'rating' => 4.6, 'stock' => 60, 'is_new' => false, 'sizes' => ['Small', 'Medium'], 'description' => 'A jungle cactus that blooms in pink or red around the winter holidays.'],
        ['name' => 'String of Pearls', 'category' => 'Succulents', 'price' => 49, 'old_price' => 69, 'rating' => 4.2, 'stock' => 37, 'is_new' => false, 'sizes' => ['Small'], 'description' => 'Cascading bead-like leaves that spill over shelf edges in bright light.'],
        ['name' => 'Haworthia Fasciata', 'category' => 'Succulents', 'price' => 32, 'old_price' => null, 'rating' => 4.3, 'stock' => 78, 'is_new' => false, 'sizes' => ['Small'], 'description' => 'Zebra plant with rigid dark rosettes and bold white tubercles.'],
        ['name' => 'Burro Tail Sedum', 'category' => 'Succulents', 'price' => 42, 'old_price' => null, 'rating' => 4.5, 'stock' => 52, 'is_new' => true, 'sizes' => ['Small'], 'description' => 'Plump grey-green tails of trailing foliage that root from any fallen leaf.'],
        ['name' => 'Mini Cactus Garden', 'category' => 'Terrariums', 'price' => 89, 'old_price' => 109, 'rating' => 4.4, 'stock' => 25, 'is_new' => false, 'sizes' => ['Small'], 'description' => 'A trio of miniature cacti arranged in a low stone dish with decorative grit.'],
        ['name' => 'Closed Moss Terrarium', 'category' => 'Terrariums', 'price' => 129, 'old_price' => null, 'rating' => 4.7, 'stock' => 14, 'is_new' => true, 'sizes' => ['Small', 'Medium'], 'description' => 'Self-sustaining world of cushion moss, ferns and stone under glass.'],
        ['name' => 'Open Fern Terrarium', 'category' => 'Terrariums', 'price' => 109, 'old_price' => null, 'rating' => 4.3, 'stock' => 19, 'is_new' => false, 'sizes' => ['Medium'], 'description' => 'An open glass bowl of maidenhair fern, fittonia and river pebbles.'],
        ['name' => 'Air Plant Trio', 'category' => 'Terrariums', 'price' => 59, 'old_price' => 75, 'rating' => 4.1, 'stock' => 46, 'is_new' => false, 'sizes' => ['Small'], 'description' => 'Three tillandsias to mount or display in holders, soil-free and easy.'],
        ['name' => 'Bonsai Juniper', 'category' => 'Gardening', 'price' => 199, 'old_price' => 249, 'rating' => 4.6, 'stock' => 11, 'is_new' => false, 'sizes' => ['Small', 'Medium'], 'description' => 'A shaped outdoor juniper in a ceramic tray, ready to continue training.'],
        ['name' => 'Lavender Pot', 'category' => 'Gardening', 'price' => 69, 'old_price' => null, 'rating' => 4.8, 'stock' => 58, 'is_new' => false, 'sizes' => ['Small', 'Medium'], 'description' => 'Fragrant English lavender in a terracotta pot, loved by bees and balconies.'],
        ['name' => 'Rosemary Standard', 'category' => 'Gardening', 'price' => 75, 'old_price' => null, 'rating' => 4.5, 'stock' => 30, 'is_new' => true, 'sizes' => ['Medium'], 'description' => 'A standards-trained rosemary topiary that is both herb and sculpture.'],
        ['name' => 'Herb Seed Kit', 'category' => 'Seeds', 'price' => 39, 'old_price' => 49, 'rating' => 4.2, 'stock' => 110, 'is_new' => false, 'sizes' => ['Small'], 'description' => 'Basil, thyme, parsley and mint seeds with peat-free compost discs.'],
        ['name' => 'Wildflower Mix', 'category' => 'Seeds', 'price' => 25, 'old_price' => null, 'rating' => 4.4, 'stock' => 140, 'is_new' => false, 'sizes' => ['Small'], 'description' => 'A pollinator-friendly blend of annuals for a cheerful summer border.'],
        ['name' => 'Tomato Seed Set', 'category' => 'Seeds', 'price' => 31, 'old_price' => null, 'rating' => 4.3, 'stock' => 95, 'is_new' => true, 'sizes' => ['Small'], 'description' => 'Cherry, beefsteak and plum varieties for a productive greenhouse summer.'],
        ['name' => 'Succulent Cuttings Box', 'category' => 'Seeds', 'price' => 47, 'old_price' => 65, 'rating' => 4.6, 'stock' => 40, 'is_new' => false, 'sizes' => ['Small'], 'description' => 'Twelve rooted succulent cuttings packed in shredded paper for safe transit.'],
        ['name' => 'Ceramic Planter Set', 'category' => 'Accessories', 'price' => 85, 'old_price' => 99, 'rating' => 4.5, 'stock' => 65, 'is_new' => false, 'sizes' => ['Small', 'Medium'], 'description' => 'Three matte-glazed ceramic planters with drainage saucers in warm neutrals.'],
        ['name' => 'Watering Can Brass', 'category' => 'Accessories', 'price' => 55, 'old_price' => null, 'rating' => 4.7, 'stock' => 48, 'is_new' => true, 'sizes' => ['Medium'], 'description' => 'A long-spout brass watering can that reaches the back of a crowded shelf.'],
        ['name' => 'Pruning Shears', 'category' => 'Accessories', 'price' => 35, 'old_price' => 45, 'rating' => 4.4, 'stock' => 80, 'is_new' => false, 'sizes' => ['Small'], 'description' => 'Stainless bypass shears with a soft grip for clean stem cuts.'],
        ['name' => 'Plant Mister', 'category' => 'Accessories', 'price' => 22, 'old_price' => null, 'rating' => 4.1, 'stock' => 130, 'is_new' => false, 'sizes' => ['Small'], 'description' => 'A fine glass mister for tropical foliage that likes humid air.'],
        ['name' => 'Hanging Macrame', 'category' => 'Accessories', 'price' => 45, 'old_price' => 59, 'rating' => 4.3, 'stock' => 55, 'is_new' => false, 'sizes' => ['Small', 'Medium'], 'description' => 'Hand-knotted natural cotton hanger for pots up to twenty centimetres.'],
        ['name' => 'Moisture Meter', 'category' => 'Accessories', 'price' => 19, 'old_price' => null, 'rating' => 4.0, 'stock' => 150, 'is_new' => true, 'sizes' => ['Small'], 'description' => 'Probe meter that reads soil moisture at root depth, no batteries needed.'],
    ];

    public function run(ProductImageFetcher $fetcher): void
    {
        foreach (self::PRODUCTS as $index => $data) {
            $category = Category::where('slug', Str::slug($data['category']))->first();

            if ($category === null) {
                continue;
            }

            $product = Product::updateOrCreate(
                ['sku' => 'GS-'.str_pad((string) ($index + 1), 5, '0', STR_PAD_LEFT)],
                [
                    'category_id' => $category->id,
                    'name' => $data['name'],
                    'slug' => Str::slug($data['name']),
                    'short_description' => $data['description'],
                    'description' => $data['description']."\n\nEvery plant is shipped in a nursery pot so it can be potted on immediately, and each order is packed by hand in our Farmingdale greenhouse just before despatch.",
                    'price' => $data['price'],
                    'old_price' => $data['old_price'],
                    'discount_percent' => null,
                    'rating' => $data['rating'],
                    'reviews_count' => random_int(3, 25),
                    'stock' => $data['stock'],
                    'is_new' => $data['is_new'],
                    'sizes' => $data['sizes'],
                    'sold_count' => random_int(5, 200),
                ],
            );

            if ($product->images()->count() === 0) {
                $fetcher->attachToProduct($product, $data['name'].' plant', 3);
            }
        }

        Coupon::updateOrCreate(
            ['code' => 'GREEN10'],
            [
                'type' => 'percent',
                'value' => 10,
                'min_order_total' => 50,
                'is_active' => true,
                'expires_at' => now()->addYear(),
            ],
        );

        Coupon::updateOrCreate(
            ['code' => 'SAVE20'],
            [
                'type' => 'fixed',
                'value' => 20,
                'min_order_total' => 150,
                'is_active' => true,
                'expires_at' => now()->addMonths(6),
            ],
        );
    }
}
