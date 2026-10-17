<dialog id="login-dialog" tabindex="-1" aria-labelledby="login-dialog-title">
    <div class="dialog-card">
        <button class="dialog-close" type="button" data-dialog-close aria-label="Close dialog">
            <span aria-hidden="true">A-</span>
        </button>

        <img class="auth-logo" src="{{ asset('assets/images/logo-stacked.svg') }}" width="158" height="91" alt="{{ config('app.name', 'GreenShop') }}">
        <p class="auth-title" aria-hidden="true">Login</p>

        <nav class="auth-tabs" aria-label="Account">
            <a href="{{ route('login') }}">Login</a>
            <span class="sep" aria-hidden="true">|</span>
            <a href="{{ route('register') }}">Register</a>
        </nav>

        <form class="auth-form" method="post" action="{{ route('login') }}">
            @csrf
            <p class="auth-lead" id="login-dialog-title">Enter your username and password to login.</p>

            @if($errors->any())
                <p class="form-status" role="alert">{{ $errors->first() }}</p>
            @endif

            <label class="visually-hidden" for="login-dialog-email">Email address</label>
            <input class="input" id="login-dialog-email" type="email" name="email" value="{{ old('email') }}" placeholder="almamun_uxui@outlook.com" autocomplete="email" required>

            <label class="visually-hidden" for="login-dialog-password">Password</label>
            <span class="input-wrap">
                <input class="input" id="login-dialog-password" type="password" name="password" autocomplete="current-password" required>
                <button class="input-wrap__toggle" type="button" data-toggle-password="login-dialog-password" aria-pressed="false" aria-label="Show password">
                    <img src="{{ asset('assets/images/icons/icon-eye-off.svg') }}" width="20" height="20" alt="">
                </button>
            </span>

            <p class="auth-links"><a href="{{ route('password.request') }}">Forgot Password?</a></p>

            <input type="hidden" name="remember" value="1">
            <button class="btn btn--primary btn--block" type="submit">Login</button>
        </form>

        <p class="auth-foot">Don't have an account? <a href="{{ route('register') }}">Sign Up</a></p>
    </div>
</dialog>

<dialog id="register-dialog" tabindex="-1" aria-labelledby="register-dialog-title">
    <div class="dialog-card">
        <button class="dialog-close" type="button" data-dialog-close aria-label="Close dialog">
            <span aria-hidden="true">A-</span>
        </button>

        <img class="auth-logo" src="{{ asset('assets/images/logo-stacked.svg') }}" width="158" height="91" alt="{{ config('app.name', 'GreenShop') }}">
        <p class="auth-title" aria-hidden="true">Sign Up</p>

        <nav class="auth-tabs" aria-label="Account">
            <a href="{{ route('login') }}">Login</a>
            <span class="sep" aria-hidden="true">|</span>
            <a href="{{ route('register') }}">Register</a>
        </nav>

        <form class="auth-form" method="post" action="{{ route('register') }}">
            @csrf
            <p class="auth-lead" id="register-dialog-title">Enter your email and password to register.</p>

            @if($errors->any())
                <p class="form-status" role="alert">{{ $errors->first() }}</p>
            @endif

            <label class="visually-hidden" for="register-dialog-name">Username</label>
            <input class="input" id="register-dialog-name" type="text" name="name" value="{{ old('name') }}" placeholder="Username" autocomplete="username" required>

            <label class="visually-hidden" for="register-dialog-email">Email address</label>
            <input class="input" id="register-dialog-email" type="email" name="email" value="{{ old('email') }}" placeholder="Enter your email address" autocomplete="email" required>

            <label class="visually-hidden" for="register-dialog-password">Password</label>
            <span class="input-wrap">
                <input class="input" id="register-dialog-password" type="password" name="password" placeholder="Password" autocomplete="new-password" minlength="8" required>
                <button class="input-wrap__toggle" type="button" data-toggle-password="register-dialog-password" aria-pressed="false" aria-label="Show password">
                    <img src="{{ asset('assets/images/icons/icon-eye-off.svg') }}" width="20" height="20" alt="">
                </button>
            </span>

            <label class="visually-hidden" for="register-dialog-confirm">Confirm password</label>
            <span class="input-wrap">
                <input class="input" id="register-dialog-confirm" type="password" name="password_confirmation" placeholder="Confirm Password" autocomplete="new-password" minlength="8" required>
                <button class="input-wrap__toggle input-wrap__toggle--mobile" type="button" data-toggle-password="register-dialog-confirm" aria-pressed="false" aria-label="Show password">
                    <img src="{{ asset('assets/images/icons/icon-eye-off.svg') }}" width="20" height="20" alt="">
                </button>
            </span>

            <button class="btn btn--primary btn--block" type="submit">
                <span class="lbl--wide">Register</span>
                <span class="lbl--narrow">Create an account</span>
            </button>
        </form>

        <p class="auth-foot">Already have an account? <a href="{{ route('login') }}">Login</a></p>
    </div>
</dialog>

<dialog id="forgot-dialog" tabindex="-1" aria-labelledby="forgot-dialog-title">
    <div class="dialog-card dialog-card--pad">
        <button class="dialog-close" type="button" data-dialog-close aria-label="Close dialog">
            <span aria-hidden="true">A-</span>
        </button>

        <img class="auth-logo" src="{{ asset('assets/images/logo-stacked.svg') }}" width="158" height="91" alt="{{ config('app.name', 'GreenShop') }}">
        <p class="auth-title" aria-hidden="true">Forgot Password?</p>

        <nav class="auth-tabs" aria-label="Account">
            <a href="{{ route('login') }}">Login</a>
            <span class="sep" aria-hidden="true">|</span>
            <a href="{{ route('register') }}">Register</a>
        </nav>

        <form class="auth-form" method="post" action="{{ route('password.email') }}">
            @csrf
            <p class="auth-lead" id="forgot-dialog-title">Enter your email to reset your password.</p>

            <label class="visually-hidden" for="forgot-dialog-email">Email address</label>
            <input class="input" id="forgot-dialog-email" type="email" name="email" value="{{ old('email') }}" placeholder="Email address" autocomplete="email" required>

            <button class="btn btn--primary btn--block" type="submit">Send Reset Link</button>
        </form>

        <p class="auth-links"><a href="{{ route('login') }}" data-dialog="login-dialog">Back to Login</a></p>
    </div>
</dialog>
