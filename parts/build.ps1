$root = "C:\Users\notebook\Desktop\figma-mcp-context-opencode"
$raw = [System.IO.File]::ReadAllText("$root\index.html")
$marker = '<main id="main">'
$i1 = $raw.IndexOf($marker)
$i2 = $raw.IndexOf('</main>', $i1)
if ($i1 -lt 0 -or $i2 -lt 0) { throw "markers not found" }
$pre = $raw.Substring(0, $i1)
$post = $raw.Substring($i2 + '</main>'.Length)

function Get-Part([string]$name) {
  return ([System.IO.File]::ReadAllText("$root\parts\$name")).TrimEnd("`r", "`n")
}

function Set-Title([string]$text, [string]$title) {
  return [regex]::Replace($text, '(?s)<title>.*?</title>', "<title>$title</title>")
}

function Set-Nav([string]$text, [string]$mode) {
  $homeActive = '<li><a href="index.html" aria-current="page">Home</a></li>'
  $homePlain  = '<li><a href="index.html">Home</a></li>'
  $shopActive = '<li><a href="product.html" aria-current="page">Shop</a></li>'
  $shopPlain  = '<li><a href="product.html">Shop</a></li>'
  if ($mode -eq 'home') { $text = $text.Replace($homePlain, $homeActive).Replace($shopActive, $shopPlain) }
  elseif ($mode -eq 'shop') { $text = $text.Replace($homeActive, $homePlain).Replace($shopPlain, $shopActive) }
  else { $text = $text.Replace($homeActive, $homePlain).Replace($shopActive, $shopPlain) }
  return $text
}

function Build-Page([string]$file, [string]$title, [string]$part, [string]$nav, [switch]$NoFooter) {
  $head = Set-Nav (Set-Title $pre $title) $nav
  $tail = $post
  if ($NoFooter) {
    $start = $tail.IndexOf('<!-- ========================== Footer')
    $end = $tail.IndexOf('</footer>') + '</footer>'.Length
    if ($start -ge 0 -and $end -gt $start) { $tail = $tail.Remove($start, $end - $start).TrimEnd() }
  }
  $body = $head + $marker + "`r`n" + (Get-Part $part) + "`r`n    " + $tail
  [System.IO.File]::WriteAllText("$root\$file", $body)
  "wrote $file ($($body.Length) chars)"
}

$thanks = ([System.IO.File]::ReadAllText("$root\parts\thanks-dialog.html")).TrimEnd("`r", "`n")

Build-Page 'product.html' 'Barberton Daisy - GreenShop' 'product-main.html' 'shop'
Build-Page 'cart.html'    'Shopping Cart - GreenShop'   'cart-main.html'    'shop'
Build-Page 'checkout.html' 'Checkout - GreenShop'       'checkout-main.html' 'shop'
Build-Page 'account.html' 'My Account - GreenShop'      'account-main.html' 'none' -NoFooter
Build-Page 'address.html' 'Address - GreenShop'         'address-main.html' 'none' -NoFooter

# checkout gets the confirmation dialog (opened on submit)
$c = [System.IO.File]::ReadAllText("$root\checkout.html")
$c = $c.Replace('</body>', $thanks + "`r`n  </body>")
[System.IO.File]::WriteAllText("$root\checkout.html", $c)

# order-confirmation = checkout with the dialog opened on load
$o = $c.Replace('<dialog id="thanks-dialog" tabindex="-1" aria-labelledby="thanks-dialog-title">',
                '<dialog id="thanks-dialog" tabindex="-1" data-autoshow="true" aria-labelledby="thanks-dialog-title">')
$o = Set-Title $o 'Order Confirmation - GreenShop'
[System.IO.File]::WriteAllText("$root\order-confirmation.html", $o)
"checkout + order-confirmation updated"

# standalone login / register pages
$idx = $raw
$l = Set-Title $idx 'Login - GreenShop'
$l = $l.Replace('<dialog id="login-dialog" tabindex="-1" aria-labelledby="login-dialog-title">',
                '<dialog id="login-dialog" tabindex="-1" data-autoshow="true" aria-labelledby="login-dialog-title">')
$l = $l.Replace('<a href="login.html">Login</a>',
                '<a href="login.html" aria-current="page">Login</a>')
[System.IO.File]::WriteAllText("$root\login.html", $l)

$r = Set-Title $idx 'Register - GreenShop'
$r = $r.Replace('<dialog id="register-dialog" tabindex="-1" aria-labelledby="register-dialog-title">',
                '<dialog id="register-dialog" tabindex="-1" data-autoshow="true" aria-labelledby="register-dialog-title">')
$r = $r.Replace('<a href="register.html">Register</a>',
                '<a href="register.html" aria-current="page">Register</a>')
[System.IO.File]::WriteAllText("$root\register.html", $r)
"login + register updated"
