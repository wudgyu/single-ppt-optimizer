export interface ThemeDefinition {
  name: string;
  widthInches: number;
  heightInches: number;
}

export const themeRegistry: Record<string, ThemeDefinition> = {
  professional_tech_dark: {
    name: "professional_tech_dark",
    widthInches: 13.333,
    heightInches: 7.5,
  },
};

export function resolveTheme(name: string): ThemeDefinition | undefined {
  return themeRegistry[name];
}
