<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

/**
 * @property int $id
 * @property int $user_id
 * @property string $label
 * @property string $full_name
 * @property string|null $phone
 * @property string $street
 * @property string $city
 * @property string|null $region
 * @property string|null $postal_code
 * @property string $country
 * @property bool $is_default
 */
class Address extends Model
{
    protected $fillable = [
        'user_id', 'label', 'full_name', 'phone', 'street', 'city',
        'region', 'postal_code', 'country', 'is_default',
    ];

    protected function casts(): array
    {
        return ['is_default' => 'boolean'];
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function getFullLineAttribute(): string
    {
        return collect([$this->street, $this->city, $this->region, $this->postal_code])
            ->filter()
            ->implode(', ');
    }
}
