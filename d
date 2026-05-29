[1mdiff --git a/.github/workflows/daily_job_hunt.yml b/.github/workflows/daily_job_hunt.yml[m
[1mindex d134042..88e8453 100644[m
[1m--- a/.github/workflows/daily_job_hunt.yml[m
[1m+++ b/.github/workflows/daily_job_hunt.yml[m
[36m@@ -20,9 +20,13 @@[m [mjobs:[m
         with:[m
           python-version: '3.12'[m
 [m
[31m-      # ⚠️ CORRECTION : libasound2t64 au lieu de libasound2[m
[32m+[m[32m      # Nettoyage du cache APT[m
[32m+[m[32m      - name: Clean APT cache[m
[32m+[m[32m        run: sudo apt-get clean && sudo apt-get update[m
[32m+[m
[32m+[m[32m      # Installation des dépendances système (avec les deux alternatives pour libasound2)[m
       - name: Install Playwright system dependencies[m
[31m-        run: sudo apt-get update && sudo apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2t64[m
[32m+[m[32m        run: sudo apt-get update && sudo apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2t64 liboss4-salsa-asound2[m
 [m
       - name: Install Python dependencies[m
         run: |[m
