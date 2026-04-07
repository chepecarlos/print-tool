from __future__ import annotations

from typing import Any, Callable, Literal, Optional, Union

from nicegui.elements.select import Select
from nicegui.elements.mixins.validation_element import ValidationDict, ValidationFunction
from nicegui.events import Handler, ValueChangeEventArguments


class TokenSearchSelect(
    Select,
    component="token_search_select.js",
):
    def __init__(
        self,
        options: Union[list, dict],
        *,
        label: Optional[str] = None,
        value: Any = None,
        on_change: Optional[Handler[ValueChangeEventArguments]] = None,
        with_input: bool = False,
        new_value_mode: Optional[Literal["add", "add-unique", "toggle"]] = None,
        multiple: bool = False,
        clearable: bool = False,
        validation: Optional[Union[ValidationFunction, ValidationDict]] = None,
        key_generator: Optional[Union[Callable[[Any], Any], Any]] = None,
    ) -> None:
        super().__init__(
            options,
            label=label,
            value=value,
            on_change=on_change,
            with_input=with_input,
            new_value_mode=new_value_mode,
            multiple=multiple,
            clearable=clearable,
            validation=validation,
            key_generator=key_generator,
        )

    def _option_meta(self, index: int) -> tuple[Any, Any]:
        label = self._labels[index]
        search_label = label
        if isinstance(self.options, dict):
            raw_value = self._values[index]
            meta = self.options.get(raw_value)
            if isinstance(meta, dict):
                label = meta.get("display_label", meta.get("label", label))
                search_label = meta.get("search_label", meta.get("label", label))
        return label, search_label

    def _value_to_model_value(self, value: Any) -> Any:
        if self.multiple:
            result = []
            for item in value or []:
                try:
                    index = self._values.index(item)
                    display_label, search_label = self._option_meta(index)
                    result.append(
                        {
                            "value": index,
                            "label": display_label,
                            "display_label": display_label,
                            "search_label": search_label,
                        }
                    )
                except ValueError:
                    pass
            return result

        try:
            index = self._values.index(value)
            display_label, search_label = self._option_meta(index)
            return {
                "value": index,
                "label": display_label,
                "display_label": display_label,
                "search_label": search_label,
            }
        except ValueError:
            return None

    def _update_options(self) -> None:
        before_value = self.value
        option_rows = []
        for index, option in enumerate(self._labels):
            display_label, search_label = self._option_meta(index)
            option_rows.append(
                {
                    "value": index,
                    "label": display_label,
                    "display_label": display_label,
                    "search_label": search_label,
                }
            )
        self._props["options"] = option_rows
        self._props[self.VALUE_PROP] = self._value_to_model_value(before_value)
        if not isinstance(before_value, list):
            self.value = before_value if before_value in self._values else None
