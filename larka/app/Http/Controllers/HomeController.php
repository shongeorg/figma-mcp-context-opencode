<?php

namespace App\Http\Controllers;

use App\Services\CatalogService;
use Illuminate\Contracts\View\View;
use Illuminate\Http\Request;

class HomeController extends Controller
{
    public function __construct(private readonly CatalogService $catalog) {}

    public function __invoke(Request $request): View
    {
        $data = $this->catalog->data($request);

        return view('home', $data + [
            'filterAction' => route('home'),
        ]);
    }
}
