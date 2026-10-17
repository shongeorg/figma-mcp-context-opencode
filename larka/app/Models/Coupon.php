<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Carbon;

/**
 * @property int $id
 * @property string $code
 * @property string $type
 * @property float $value
 * @property float $min_order_total
 * @property bool $is_active
 * @property int|null $usage_limit
 * @property int $used_count
 * @property Carbon|null $expires_at
 */
class Coupon extends Model
{
    public const TYPE_PERCENT = 'percent';

    public const TYPE_FIXED = 'fixed';

    protected $fillable = [
        'code', 'type', 'value', 'min_order_total', 'is_active',
        'usage_limit', 'used_count', 'expires_at',
    ];

    protected function casts(): array
    {
        return [
            'value' => 'float',
            'min_order_total' => 'float',
            'is_active' => 'boolean',
            'expires_at' => 'datetime',
        ];
    }

    public function isValidFor(float $subtotal): bool
    {
        if (! $this->is_active) {
            return false;
        }

        if ($this->expires_at && $this->expires_at->isPast()) {
            return false;
        }

        if ($this->usage_limit !== null && $this->used_count >= $this->usage_limit) {
            return false;
        }

        return $subtotal >= $this->min_order_total;
    }

    public function discountFor(float $subtotal): float
    {
        $discount = $this->type === self::TYPE_PERCENT
            ? $subtotal * $this->value / 100
            : $this->value;

        return round(min($discount, $subtotal), 2);
    }
}
