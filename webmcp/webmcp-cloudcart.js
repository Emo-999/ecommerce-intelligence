/* webmcp-cloudcart.js
 * ===================
 * WebMCP слой за CloudCart магазини: излага инструменти на браузърни AI
 * агенти (Chrome 149+, origin trial) БЕЗ каквато и да е промяна по бекенда.
 * Инсталира се от търговеца: Контролен панел -> Моят магазин ->
 * Custom CSS/JS -> поставете този файл в JS редактора. Скриптът работи в
 * контекста на витрината и ползва само публичните AJAX крайни точки, които
 * самата тема вика (проверени на 7+ живи магазина, 2026-08).
 *
 * API по спецификацията (webmachinelearning.github.io/webmcp):
 *   document.modelContext.registerTool({name, title, description,
 *     inputSchema, execute, annotations})
 * (navigator.modelContext е останалото име в Chrome 149, deprecated в 150.)
 *
 * Ако браузърът няма WebMCP, скриптът не прави нищо (никакъв ефект за
 * обикновените посетители).
 */
(function () {
  'use strict';

  /* Ако имате origin-trial токен за домейна си (регистрация:
   * developer.chrome.com/origintrials — WebMCP), поставете го тук.
   * Токенът може да се подаде и от JS чрез meta таг: */
  var ORIGIN_TRIAL_TOKEN = '';
  if (ORIGIN_TRIAL_TOKEN) {
    var m = document.createElement('meta');
    m.httpEquiv = 'origin-trial';
    m.content = ORIGIN_TRIAL_TOKEN;
    document.head.appendChild(m);
  }

  var mc = document.modelContext || navigator.modelContext;
  if (!mc || typeof mc.registerTool !== 'function') return;

  var XHR = { 'X-Requested-With': 'XMLHttpRequest' };

  function asText(obj) {
    var text = typeof obj === 'string' ? obj : JSON.stringify(obj);
    return { content: [{ type: 'text', text: text }] };
  }
  function fail(msg) { return asText({ error: msg }); }

  function fetchJson(url, opts) {
    return fetch(url, opts).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status + ' за ' + url);
      return r.json();
    });
  }

  /* Продуктова страница -> структурирани данни: JSON-LD (schema.org
   * Product) + пълният масив варианти от data-variant-selection. */
  function parseProductDoc(doc, url) {
    var out = { url: url, name: null, description: null, price: null,
                currency: null, availability: null, images: [],
                product_id: null, variants: [] };
    var scripts = doc.querySelectorAll('script[type="application/ld+json"]');
    for (var i = 0; i < scripts.length; i++) {
      try {
        var ld = JSON.parse(scripts[i].textContent);
        if (ld && ld['@type'] === 'Product') {
          out.name = ld.name || null;
          out.description = (ld.description || '').slice(0, 500) || null;
          if (ld.image) out.images = [].concat(ld.image).slice(0, 3);
          var offer = [].concat(ld.offers || [])[0] || {};
          out.price = offer.price || null;
          out.currency = offer.priceCurrency || null;
          out.availability = offer.availability || null;
          break;
        }
      } catch (e) { /* следващият скрипт */ }
    }
    /* data-variant-selection е ВЛОЖЕН обект по стойности на опциите
     * ({"Опция1":{"Опция2":[варианти]}}; празни низове без опции) —
     * събираме всички масиви рекурсивно. */
    function collect(node, acc) {
      if (Array.isArray(node)) { acc.push.apply(acc, node); }
      else if (node && typeof node === 'object') {
        Object.keys(node).forEach(function (k) { collect(node[k], acc); });
      }
      return acc;
    }
    var pidInput = doc.querySelector('input[name="product_id"]');
    if (pidInput) out.product_id = pidInput.value;
    var vEl = doc.querySelector('[data-variant-selection]');
    if (vEl) {
      out.default_variant_id =
        vEl.getAttribute('data-variant-default') || null;
      try {
        var flat = collect(
          JSON.parse(vEl.getAttribute('data-variant-selection')), []);
        out.variants = flat.map(function (v) {
          if (!out.product_id && v.item_id) out.product_id = String(v.item_id);
          return { variant_id: v.id, sku: v.sku || null,
                   option1: v.v1 || null, option2: v.v2 || null,
                   option3: v.v3 || null,
                   /* платформата пази цените в стотинки (×100) */
                   price: v.price != null ? v.price / 100 : null,
                   in_stock: v.stock_status_key !== 'out-of-stock',
                   quantity: v.quantity };
        });
      } catch (e) { /* остава празно */ }
    }
    return out;
  }

  /* -------------------------------------------------- search_products */
  mc.registerTool({
    name: 'search_products',
    title: 'Търсене на продукти',
    description: 'Search this store\'s product catalogue by keyword. ' +
      'Returns up to 10 matches with name, URL, image and category. ' +
      'Use get_product_details on a result URL before adding to cart.',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string',
                 description: 'Search terms, minimum 2 characters' }
      },
      required: ['query']
    },
    annotations: { readOnlyHint: true },
    execute: async function (input) {
      try {
        var q = String(input.query || '').trim();
        if (q.length < 2) return fail('Заявката трябва да е поне 2 знака.');
        var hits = await fetchJson(
          '/widget/search/autocomplete?term=' + encodeURIComponent(q),
          { headers: XHR });
        var items = (hits || []).slice(0, 10).map(function (h) {
          return { name: h.name, url: h.url, image: h.image || null,
                   category: h.category || null };
        });
        return asText({ query: q, results: items,
                        note: items.length ? undefined
                              : 'Няма съвпадения за тази заявка.' });
      } catch (e) { return fail(String(e)); }
    }
  });

  /* --------------------------------------------- get_product_details */
  mc.registerTool({
    name: 'get_product_details',
    title: 'Детайли за продукт',
    description: 'Get structured details for a product: price, currency, ' +
      'availability, description and the variant list with variant_id ' +
      'values required by add_to_cart. Omit url to read the product page ' +
      'the user is currently viewing.',
    inputSchema: {
      type: 'object',
      properties: {
        url: { type: 'string',
               description: 'Product page URL on this store (optional)' }
      }
    },
    annotations: { readOnlyHint: true },
    execute: async function (input) {
      try {
        if (!input.url) {
          var here = parseProductDoc(document, location.href);
          if (!here.variants.length && !here.name)
            return fail('Текущата страница не е продуктова. Подайте url.');
          return asText(here);
        }
        var u = new URL(input.url, location.origin);
        if (u.origin !== location.origin)
          return fail('Инструментът работи само с адреси от този магазин.');
        var html = await fetch(u.href, { headers: XHR }).then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.text();
        });
        var doc = new DOMParser().parseFromString(html, 'text/html');
        return asText(parseProductDoc(doc, u.href));
      } catch (e) { return fail(String(e)); }
    }
  });

  /* --------------------------------------------------- add_to_cart */
  mc.registerTool({
    name: 'add_to_cart',
    title: 'Добавяне в количката',
    description: 'Add a product variant to the shopping cart. Requires ' +
      'product_id and variant_id from get_product_details. The user ' +
      'completes checkout themselves; this only prepares the cart.',
    inputSchema: {
      type: 'object',
      properties: {
        product_id: { type: 'string', description: 'Numeric product id' },
        variant_id: { type: 'string', description: 'Numeric variant id' },
        quantity: { type: 'integer', minimum: 1, default: 1 }
      },
      required: ['product_id', 'variant_id']
    },
    execute: async function (input) {
      try {
        var body = new URLSearchParams();
        body.set('product_id', String(input.product_id));
        body.set('variant_id', String(input.variant_id));
        body.set('quantity', String(input.quantity || 1));
        var res = await fetchJson('/cart/add', {
          method: 'POST',
          headers: Object.assign({
            'Content-Type': 'application/x-www-form-urlencoded'
          }, XHR),
          body: body.toString()
        });
        if (res.status !== 'success')
          return fail('Магазинът отказа добавянето: ' + JSON.stringify(res));
        var p = res.product || {};
        return asText({ added: true, product: p.name || null,
                        quantity: res.quantity || input.quantity || 1,
                        currency: res.currency || null,
                        message: 'Продуктът е в количката. Потребителят ' +
                                 'довършва поръчката от страницата на ' +
                                 'количката.' });
      } catch (e) { return fail(String(e)); }
    }
  });

  /* ----------------------------------------------------- view_cart */
  mc.registerTool({
    name: 'view_cart',
    title: 'Преглед на количката',
    description: 'Read the current shopping cart contents as text ' +
      '(items, quantities, totals).',
    inputSchema: { type: 'object', properties: {} },
    annotations: { readOnlyHint: true },
    execute: async function () {
      try {
        var res = await fetchJson('/cart/panel', { headers: XHR });
        var doc = new DOMParser().parseFromString(res.html || '',
                                                  'text/html');
        var txt = (doc.body.textContent || '')
          .replace(/\s+/g, ' ').trim().slice(0, 1200);
        return asText({ title: res.title || 'Количка', contents: txt });
      } catch (e) { return fail(String(e)); }
    }
  });

  /* ------------------------------------------------ get_store_info */
  mc.registerTool({
    name: 'get_store_info',
    title: 'Информация за магазина',
    description: 'Basic store facts: name, currency, current page type.',
    inputSchema: { type: 'object', properties: {} },
    annotations: { readOnlyHint: true },
    execute: async function () {
      var cc = window.ccsettings || {};
      return asText({
        name: document.title,
        origin: location.origin,
        currency: cc.currency || null,
        locale: document.documentElement.lang || null
      });
    }
  });
})();
