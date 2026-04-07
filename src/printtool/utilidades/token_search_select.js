const STYLE_ID = "token-search-select-style";

export default {
  props: ["options"],
  template: `
    <q-select
      ref="qRef"
      class="token-search-select"
      :options="filteredOptions"
      :option-label="optionLabel"
      @filter="filterFn"
      @popup-show="addClass"
      @popup-hide="removeClass"
    >
      <template v-for="(_, slot) in $slots" v-slot:[slot]="slotProps">
        <slot :name="slot" v-bind="slotProps || {}" />
      </template>
    </q-select>
  `,
  data() {
    return {
      initialOptions: this.options,
      filteredOptions: this.options,
    };
  },
  methods: {
    ensureStyle() {
      if (document.getElementById(STYLE_ID)) return;
      const style = document.createElement("style");
      style.id = STYLE_ID;
      style.textContent = `
        .token-search-select input[type="search"]::-webkit-search-cancel-button {
          -webkit-appearance: none;
          appearance: none;
          display: none;
        }
        .token-search-select input[type="search"]::-ms-clear,
        .token-search-select input[type="search"]::-ms-reveal {
          display: none;
          width: 0;
          height: 0;
        }
      `;
      document.head.appendChild(style);
    },
    optionLabel(option) {
      return option?.display_label ?? option?.label ?? "";
    },
    filterFn(val, update, abort) {
      update(() => (this.filteredOptions = val ? this.findFilteredOptions() : this.initialOptions));
    },
    normalizeTerms(value) {
      const values = Array.isArray(value) ? value : [value];
      return values
        .flatMap((entry) =>
          String(entry ?? "")
            .toLocaleLowerCase()
            .replace(/[|,/_()]+/g, " ")
            .split(/\s+/),
        )
        .map((token) => token.trim())
        .filter(Boolean);
    },
    splitQueryTokens(value) {
      return String(value ?? "")
        .toLocaleLowerCase()
        .trim()
        .split(/\s+/)
        .map((token) => token.trim())
        .filter(Boolean)
        .map((token) => ({ exclude: token.startsWith("-"), token: token.startsWith("-") ? token.slice(1) : token }))
        .filter((item) => item.token);
    },
    findFilteredOptions() {
      const needle = this.$el.querySelector("input[type=search]")?.value ?? "";
      const queryTokens = this.splitQueryTokens(needle);
      if (!queryTokens.length) return this.initialOptions;

      const includeTokens = queryTokens.filter((item) => !item.exclude).map((item) => item.token);
      const excludeTokens = queryTokens.filter((item) => item.exclude).map((item) => item.token);

      return this.initialOptions.filter((option) => {
        const searchTerms = this.normalizeTerms(option.search_terms ?? option.search_label ?? option.label);
        const includeOk = includeTokens.every((token) => searchTerms.some((term) => term.includes(token)));
        const excludeOk = excludeTokens.every((token) => searchTerms.every((term) => !term.includes(token)));
        return includeOk && excludeOk;
      });
    },
    addClass() {
      document.documentElement.classList.add("nicegui-select-popup-open");
    },
    async removeClass() {
      await this.$nextTick();
      document.documentElement.classList.remove("nicegui-select-popup-open");
    },
  },
  mounted() {
    this.ensureStyle();
  },
  updated() {
    this.ensureStyle();
    if (!this.$attrs.multiple) return;
    const newFilteredOptions = this.findFilteredOptions();
    if (newFilteredOptions.length !== this.filteredOptions.length) {
      this.filteredOptions = newFilteredOptions;
    }
  },
  unmounted() {
    this.removeClass();
  },
  watch: {
    options: {
      handler(newOptions) {
        this.initialOptions = newOptions;
        this.filteredOptions = newOptions;
      },
      immediate: true,
    },
  },
};
