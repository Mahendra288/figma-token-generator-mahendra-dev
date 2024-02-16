import copy
import json
from typing import Dict, Tuple, List

import constants
from enums import RawFigmaTokensDictKeys


class GenerateFigmaTokens:

    def __init__(self):
        self.raw_data = self._read_data_from_file("raw_figma_tokens.json")

    def generate_index_css(self):
        colors = self.raw_data[RawFigmaTokensDictKeys.PRIMITIVES.value][RawFigmaTokensDictKeys.COLORS.value]
        base_css_variables, dependent_variables = self._parse_index_css_base_and_dependent_variables(
            colors=colors
        )
        processed_data = f'{{ \n{"".join(base_css_variables + dependent_variables)}\n }}'
        with open("index.css", "w") as file:
            file.write(constants.INDEX_FILE_TEMPLATE.format(css_variables=processed_data))

    def generate_tailwind_config(self):
        tw_color_variables_dict = self._parse_tw_color_variables()
        tw_spacing_variables_str = self._parse_tw_spacing_variables()
        tw_radius_variables_dict = self._parse_tw_radius_variables()
        tw_width_variables_str = self._parse_tw_width_variables()
        tw_components_plugins = self._parse_tw_components_plugins()

        output_ = constants.TAILWIND_CONFIG_FILE_TEMPLATE.format(
            colors=json.dumps(tw_color_variables_dict, indent=12),
            spacing=str(tw_spacing_variables_str),
            border_radius=json.dumps(tw_radius_variables_dict, indent=12),
            widths=tw_width_variables_str,
            componentPlugins=tw_components_plugins,
        )
        output_ = output_.replace('"<@@$$$<', "")
        output_ = output_.replace('<@@$$$<"', "")
        with open("tailwind.config.js", "w") as file:
            file.write(output_)

    def generate_directives(self):
        container_variables_dict = self._parse_directives_container_variables()
        width_variables_dict = self._parse_directives_width_variables()
        spacing_variables_dict = self._prep_directives_spacing_variables()

        components_str = self._prep_directives_components_str(
            container_variables_dict=container_variables_dict,
            spacing_variables_dict=spacing_variables_dict,
            width_variables_dict=width_variables_dict
        )

        output_ = constants.DIRECTIVES_TEMPLATE.format(
            components=components_str,
            utilities="",
        )
        with open("directives.css", "w") as file:
            file.write(output_)

    def _prep_directives_spacing_variables(self) -> Dict:
        spacing = self.raw_data[RawFigmaTokensDictKeys.SPACING.value.lower()]
        spacing_variables = {}
        for dirty_variable_name in spacing.keys():
            clean_variable_name = self._generate_clean_style_name(dirty_variable_name)
            dirty_value = spacing[dirty_variable_name]["$value"]
            spacing_variables[clean_variable_name] = (
                self._generate_tailwind_spacing_var_for_reference_value(dirty_value)
            )
        return spacing_variables

    def _parse_directives_width_variables(self) -> Dict:
        width = self.raw_data[RawFigmaTokensDictKeys.WIDTH.value]
        width_variables = {}
        for dirty_variable_name in width.keys():
            clean_variable_name = self._generate_clean_style_name(dirty_variable_name)
            dirty_value = width[dirty_variable_name]["$value"]
            width_variables[clean_variable_name] = (
                self._generate_tailwind_spacing_var_for_reference_value(dirty_value)
            )
        return width_variables

    def _parse_directives_container_variables(self) -> Dict:
        containers = self.raw_data[RawFigmaTokensDictKeys.CONTAINER.value]
        container_variables = {}
        for dirty_variable_name in containers.keys():
            clean_variable_name = self._generate_clean_style_name(dirty_variable_name)
            dirty_value = containers[dirty_variable_name]["$value"]
            container_variables[clean_variable_name] = (
                self._generate_tailwind_spacing_var_for_reference_value(dirty_value)
            )
        return container_variables

    def _parse_tw_components_plugins(self) -> str:
        component_plugin_color_mapping = self._prep_component_plugin_colors()
        theme_color_variables = self._prep_theme_color_variables(component_plugin_color_mapping)
        updated_theme_color_variables = self._update_theme_color_variables(theme_color_variables)
        components_plugins_str = constants.COMPONENTS_PLUGINS_TEMPLATE.format(
            theme_color_variables=json.dumps(updated_theme_color_variables, indent=12)
        )
        return components_plugins_str

    def _prep_theme_color_variables(self, component_plugin_color_mapping: Dict) -> Dict:
        theme_color_variables = {}

        for dirty_variable_name, value in component_plugin_color_mapping.items():
            clean_variable_name = self._generate_clean_style_name(dirty_variable_name)
            updated_key = ".{}".format(clean_variable_name)

            try:
                dirty_value = value["$value"]
            except Exception as err:
                raise err

            category_name = dirty_variable_name
            if dirty_variable_name == "Text":
                category_name = "color"
            if dirty_variable_name == "Background":
                category_name = "backgroundColor"
            if dirty_variable_name == "Border":
                category_name = "borderColor"

            theme_color_variables[updated_key] = (
                self._generate_tailwind_var_for_reference_value(
                    dirty_value,
                    category_name
                )
            )
        return theme_color_variables

    def _generate_tailwind_var_for_reference_value(self, dirty_value: str, category_name: str) -> Dict:
        clean_reference_value = self._clean_var_name_for_reverence_value(dirty_value)
        return {category_name: f"<@@$$$<theme('colors.{clean_reference_value}')<@@$$$<"}

    def _prep_component_plugin_colors(self) -> Dict:
        light_theme_dict = self.raw_data[
            RawFigmaTokensDictKeys.THEME.value
        ][RawFigmaTokensDictKeys.LIGHT_THEME.value]

        component_plugin_colors = {}
        for _, value in light_theme_dict[RawFigmaTokensDictKeys.COLORS.value].items():
            component_plugin_colors.update(value)

        components_raw_dict = light_theme_dict[
            RawFigmaTokensDictKeys.COMPONENT_COLORS.value
        ]["Components"]

        component_plugin_colors.update(components_raw_dict["App store badges"])
        component_plugin_colors.update(components_raw_dict["Application navigation"])
        component_plugin_colors.update(components_raw_dict["Avatars"])
        component_plugin_colors.update(components_raw_dict["Breadcrumbs"])

        for _, value in components_raw_dict["Buttons"].items():
            component_plugin_colors.update(value)

        component_plugin_colors.update(components_raw_dict["Footers"])
        component_plugin_colors.update(components_raw_dict["Header sections"])

        component_plugin_colors.update(components_raw_dict["Icons"].get("Icons", {}))

        for _, value in components_raw_dict["Icons"].get("Featured icons", {}).items():
            component_plugin_colors.update(value)

        component_plugin_colors.update(components_raw_dict["Icons"].get("Social icons", {}))

        component_plugin_colors.update(components_raw_dict["Mockups"])
        component_plugin_colors.update(components_raw_dict["Sliders"])
        component_plugin_colors.update(components_raw_dict["Thumbnail"])
        component_plugin_colors.update(components_raw_dict["Toggles"])
        component_plugin_colors.update(components_raw_dict["Tooltips"])
        component_plugin_colors.update(components_raw_dict["WYSIWYG editor"])

        utilities_raw_dict = light_theme_dict[
            RawFigmaTokensDictKeys.COMPONENT_COLORS.value
        ]["Utility"]
        for _, value in utilities_raw_dict.items():
            component_plugin_colors.update(value)
        return component_plugin_colors

    def _parse_tw_width_variables(self) -> str:
        width_config = self.raw_data[RawFigmaTokensDictKeys.WIDTH.value]

        tw_width_variables = ""
        for key, value in width_config.items():
            width_template = "'{key}': theme({value}),\n"
            tw_width_variables += width_template.format(
                key=key.replace("width-", ""),
                value="'{}'".format(
                    ".".join(value["$value"][1:-1].lower().split()[0].split("."))
                ),
            )
        return f"{{{tw_width_variables}}}"

    def _parse_tw_color_variables(self) -> Dict:
        tw_color_variables = {}

        colors = self.raw_data[RawFigmaTokensDictKeys.PRIMITIVES.value][RawFigmaTokensDictKeys.COLORS.value]
        for cat in sorted(colors.keys()):
            for sub_cat in sorted(colors[cat].keys()):
                key_name = self._generate_clean_style_name(dirty_name="{}-{}".format(cat, sub_cat))
                tw_color_variables[key_name] = "var(--{var_name})".format(var_name=key_name)

        return tw_color_variables

    def _parse_tw_radius_variables(self) -> Dict:
        radius_config = self.raw_data[RawFigmaTokensDictKeys.RADIUS.value]
        tw_radius_variables = {}
        for key, value in radius_config.items():
            tw_radius_variables[key.replace("radius-", "")] = "{}px".format(value["$value"])

        return tw_radius_variables

    def _parse_tw_spacing_variables(self) -> str:
        primitive_spacing = self.raw_data[
            RawFigmaTokensDictKeys.PRIMITIVES.value
        ][RawFigmaTokensDictKeys.SPACING.value]

        x = "\n".join(
            [
                "{key}: '{value}px',".format(key=key.split(" ")[0], value=value["$value"])
                for key, value in primitive_spacing.items()
            ]
        )

        spacing = self.raw_data[RawFigmaTokensDictKeys.SPACING.value.lower()]
        spacing_variables = {}
        for dirty_variable_name in spacing.keys():
            clean_variable_name = self._generate_clean_style_name(dirty_variable_name)
            dirty_value = spacing[dirty_variable_name]["$value"]
            spacing_variables[clean_variable_name] = (
                self._generate_tailwind_spacing_var_for_reference_value(dirty_value)
            )

            new_key = dirty_value[1:-1].replace("Spacing.", "")
            x += "'{key}': '{value}px',\n".format(
                key=clean_variable_name.replace("spacing-", ""),
                value=primitive_spacing[new_key]["$value"],
            )

        return f"{{{x}}}"

    def _parse_index_css_base_and_dependent_variables(self, colors: Dict) -> Tuple[List[str], List[str]]:
        base_css_variables = []
        dependent_variables = []
        for cat in sorted(colors.keys()):
            for sub_cat, data in colors[cat].items():
                color = data["$value"]
                key_name = self._generate_clean_style_name(
                    dirty_name="{}-{}".format(cat, sub_cat)
                )

                if color.startswith("{"):
                    var_ = constants.CSS_VARIABLE_TEMPLATE.format(
                        key_name, self._generate_css_var_for_reference_value(color)
                    )
                    dependent_variables.append(var_)
                else:
                    var_ = constants.CSS_VARIABLE_TEMPLATE.format(key_name, color)
                    base_css_variables.append(var_)
        return base_css_variables, dependent_variables

    def _generate_tailwind_spacing_var_for_reference_value(self, val: str) -> str:
        remove_wrapping_brackets = val[1:-1]
        partially_cleaned_name = "-".join(remove_wrapping_brackets.split(" ")[:1])
        partially_cleaned_name = partially_cleaned_name.lower()
        partially_cleaned_name = partially_cleaned_name.replace("spacing", "s")

        clean_reference_value = self._generate_clean_style_name(partially_cleaned_name)
        return "@apply {clean_reference_value}".format(
            clean_reference_value=clean_reference_value
        )

    def _generate_css_var_for_reference_value(self, val: str) -> str:
        clean_reference_value = self._clean_var_name_for_reverence_value(val)
        return "var(--{clean_reference_value})".format(
            clean_reference_value=clean_reference_value
        )

    def _clean_var_name_for_reverence_value(self, val: str) -> str:
        remove_wrapping_brackets = val[1:-1]
        partially_cleaned_name = "-".join(remove_wrapping_brackets.split(".")[1:])
        clean_reference_value = self._generate_clean_style_name(partially_cleaned_name)
        return clean_reference_value

    @staticmethod
    def _generate_clean_style_name(dirty_name: str) -> str:
        return (
            dirty_name.replace(" ", "-")
            .replace(".", "-")
            .replace("(", "")
            .replace(")", "")
            .lower()
        )

    @staticmethod
    def _read_data_from_file(file_name: str) -> Dict:
        with open(f"./{file_name}", "rb") as file:
            data = json.load(file)
        return data

    @staticmethod
    def _prep_directives_components_str(
        container_variables_dict: Dict,
        spacing_variables_dict: Dict,
        width_variables_dict: Dict
    ) -> str:
        components = ""
        for key, value in container_variables_dict.items():
            components += constants.TW_VARIABLE_TEMPLATE.format(key=key, value=value)
        for key, value in width_variables_dict.items():
            components += constants.TW_VARIABLE_TEMPLATE.format(key=key, value=value)
        for key, value in spacing_variables_dict.items():
            components += constants.TW_VARIABLE_TEMPLATE.format(key=key, value=value)
        return components

    @staticmethod
    def _update_theme_color_variables(theme_color_variables: Dict) -> Dict:
        keys_to_delete = []
        updated_theme_color_variables = copy.deepcopy(theme_color_variables)
        for key, value in theme_color_variables.items():
            if "-bg" in key or "bg-" in key:
                if "backgroundColor" in value:
                    continue
                updated_theme_color_variables[key] = {"backgroundColor": list(value.values())[0]}
            elif "-border" in key or "border-" in key:
                if "backgroundColor" in value:
                    continue
                updated_theme_color_variables[key] = {"borderColor": list(value.values())[0]}
            elif (
                    ("-fg" in key or "fg-" in key) or ("utility-" in key or "-utility" in key)
            ) and "-text" not in key or "-bg" in key or "-border" in key:
                color_value = list(value.values())[0]
                updated_theme_color_variables[f".text-{key[1:]}"] = {"color": color_value}
                updated_theme_color_variables[f".bg-{key[1:]}"] = {"backgroundColor": color_value}
                updated_theme_color_variables[f".border-{key[1:]}"] = {"borderColor": color_value}
                keys_to_delete.append(key)
            else:
                updated_theme_color_variables[key] = {"color": list(value.values())[0]}

        for key_ in keys_to_delete:
            updated_theme_color_variables.pop(key_)
        return updated_theme_color_variables

if __name__ == "__main__":
    util = GenerateFigmaTokens()

    util.generate_index_css()
    util.generate_tailwind_config()
    util.generate_directives()
    print("Processing completed successfully.")
