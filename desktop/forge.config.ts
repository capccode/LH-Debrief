import type { ForgeConfig } from "@electron-forge/shared-types";
import { MakerDMG } from "@electron-forge/maker-dmg";
import { MakerZIP } from "@electron-forge/maker-zip";
import { AutoUnpackNativesPlugin } from "@electron-forge/plugin-auto-unpack-natives";

const config: ForgeConfig = {
  packagerConfig: {
    name: "LH-Debrief",
    executableName: "lh-debrief",
    icon: "./assets/icon",
    asar: true,
    extraResource: ["../api", "../src", "../pyproject.toml", "../uv.lock"],
  },
  makers: [
    new MakerDMG({ name: "LH-Debrief" }),
    new MakerZIP({}, ["darwin"]),
  ],
  plugins: [new AutoUnpackNativesPlugin({})],
};

export default config;
