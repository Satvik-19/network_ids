/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: {
    colors: {
      slate: {50:"var(--text1)",100:"var(--text1)",200:"var(--text1)",300:"var(--text2)",400:"var(--text2)",500:"var(--text3)",600:"var(--text4)",700:"var(--border-visible)",800:"var(--border)",900:"var(--surface1)",950:"var(--background)"},
      white:"var(--text1)",
      emerald:{50:"var(--surface2)",200:"var(--border)",300:"var(--text1)",400:"var(--success)",500:"var(--success)",600:"var(--success)",700:"var(--text1)"},
      amber:{50:"var(--surface2)",200:"var(--text2)",300:"var(--text1)",400:"var(--warning)",500:"var(--warning)",600:"var(--surface3)",700:"var(--surface2)"},
      orange:{50:"var(--surface2)",200:"var(--border)",300:"var(--text1)",400:"var(--high)",500:"var(--high)",700:"var(--text1)"},
      red:{50:"var(--surface2)",200:"var(--border)",300:"var(--text1)",400:"var(--error)",500:"var(--error)",600:"var(--error)",700:"var(--text1)"},
      violet:{50:"var(--surface2)",200:"var(--border)",300:"var(--text1)",400:"var(--warning)",500:"var(--warning)",700:"var(--text1)"},
      blue:{300:"var(--text1)",400:"var(--text2)",500:"var(--text2)",600:"var(--text1)",700:"var(--text2)"},
    },
    fontFamily:{sans:['IBM Plex Sans','Segoe UI','sans-serif'],mono:['IBM Plex Mono','Consolas','monospace']},
    borderRadius:{lg:'4px',xl:'4px'},
    transitionDuration:{DEFAULT:'150ms'},
  } },
  plugins: [],
};
