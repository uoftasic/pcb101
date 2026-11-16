# Tiny Tapeout's Pmod library, two files of it

| | |
|---|---|
| Source | <https://github.com/TinyTapeout/kicad-tinytapeout-pmod-lib> |
| Commit | `9ee6345a6153ca20004fca47eec910166af836d7` (2024-07-10) |
| Licence | Apache License 2.0, in [`LICENSE`](LICENSE) next to this file |
| Copied | `TinyTapeout_PMOD.kicad_sym` and `TinyTapeout_PMOD.pretty/PinHeader_2x06_P2.54mm_PMODPeriph2B.kicad_mod`, unchanged |

The symbol `PMOD_PERIPH_2x6` and the footprint `PinHeader_2x06_P2.54mm_PMODPeriph2B` are the plug side of a Pmod connector with Digilent's pin numbering: `IO1` to `IO4` on pins 1 to 4, `GND` on 5 and 11, `VCC` on 6 and 12, and `IO5` to `IO8` on pins 7 to 10. The project's `sym-lib-table` and `fp-lib-table` add them as the library `TinyTapeout_PMOD`, through `${KIPRJMOD}/lib/`, so the project opens the same way on any computer.

The library's README says that when a board has more than one Pmod connector, they sit 0.9 in (22.86 mm) apart, with the input connector on the left, the bidirectional one in the middle and the output one on the right, looking at the board from the top. The rest of the library (the "Designed for Tiny Tapeout" logos, images and SVGs) is in the repository above.
