/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'vedic-cream': '#FDFBF7',  // Main background
                'vedic-beige': '#F4EBD0',  // Secondary backgrounds
                'vedic-orange': '#FF9933', // Primary Call-to-Action (Saffron)
                'vedic-gold': '#DAA520',   // Accents
                'vedic-blue': '#1A237E',   // Headers / Footer (Deep Navy)
                'vedic-text': '#2C2520',   // Main body text
                'vedic-muted': '#6B6560',  // Muted text
            },
            fontFamily: {
                sans: ['Lato', 'sans-serif'],
                serif: ['Playfair Display', 'serif'],
            },
            backgroundImage: {
                'om-pattern': "url('https://www.transparenttextures.com/patterns/black-scales.png')", // Placeholder for subtle texture
            },
            boxShadow: {
                'vedic': '0 4px 20px rgba(0,0,0,0.08)',
                'vedic-hover': '0 10px 25px rgba(0,0,0,0.12)',
            }
        },
    },
    plugins: [],
}
