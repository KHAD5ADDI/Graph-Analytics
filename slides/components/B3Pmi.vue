<template>
  <div class="slide b3">
    <div class="eyebrow">Backup · PMI versus counts</div>
    <h1 class="h">On the same 10,853 edges, PMI finds <em>five</em> groups</h1>
    <div class="pair">
      <div><span class="num big">3</span><b>communities</b><p>weights = shared-recipe counts</p><p class="num">modularity 0.274</p></div>
      <div class="pmi"><span class="num big">5</span><b>communities</b><p>weights = PMI</p><p class="num">modularity 0.400</p></div>
    </div>
    <p class="cap">Counts reward frequent ingredients: salt and garlic look strong but are only 1.16 times chance; ginger and soy sauce are 4.46 times.</p>
  </div>
</template>
<style scoped>
.b3 .eyebrow { position: absolute; left: 140px; top: 150px; }
.b3 .h { position: absolute; left: 136px; top: 196px; margin: 0; font: 400 80px/1 var(--serif); } .b3 .h em { color: var(--pen); }
.b3 .pair { position: absolute; left: 140px; top: 400px; display: flex; gap: 220px; }
.b3 .pair div { display: flex; flex-direction: column; }
.b3 .big { font-size: 300px; line-height: .8; } .b3 .pmi .big { color: var(--pen); }
.b3 b { font: 400 50px/1.1 var(--serif); margin-top: 10px; }
.b3 p { margin: 6px 0 0; font-size: 26px; color: var(--ink-2); }
.b3 .cap { position: absolute; left: 140px; top: 905px; width: 1640px; margin: 0; font-size: 24px; color: var(--ink-2); }
</style>
