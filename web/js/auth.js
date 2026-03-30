window.Auth = {
    TOKEN_KEY: 'autoads_token',

    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    setToken(token) {
        if (token) {
            localStorage.setItem(this.TOKEN_KEY, token);
        } else {
            this.clearToken();
        }
    },

    clearToken() {
        localStorage.removeItem(this.TOKEN_KEY);
    },

    isLoggedIn() {
        return !!this.getToken();
    },
};
