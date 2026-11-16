# Photo Sources — Added Reference Anchors

These 17 photographs were added in the November 2026 fix pass to strengthen
the four monuments with only 3 reference anchors each (Elephanta Caves,
Khajuraho Temples, Red Fort, Agra Fort) and to add the new Jama Masjid entry.
Each file below exists in BOTH `backend/datasets/reference_gallery_100/<monument>/`
(the live FAISS index source) and `backend/dataset/<monument>/` (the
`index_builder.py` source and `/dataset` preview mount), under the same filename.

All photos are freely licensed Wikimedia Commons photographs. Every file was
downloaded as derivatives up to 1920px wide served by the Commons thumbnail service
from the original on the linked file page, then verified to be a real photograph
(JPEG magic bytes, dimensions, and visual inspection on 15 November 2026).
No placeholder graphics, renders, or AI-generated images are included.
Attribution: keep this file with the photos; the licences below require
attribution (and share-alike for the CC BY-SA files).

> The FAISS index was NOT rebuilt with these photos in this fix pass — see
> `FIXES_APPLIED.md` for the exact rebuild command. Until the rebuild runs,
> recognition still uses the previous 577-vector index.

| Monument | File | Commons file page | Author | Licence | Size (bytes) |
|---|---|---|---|---|---|
| `agra_fort` | `ref_04.jpg` | [File:Amar Singh Gate, Agra Fort, Agra.jpg](https://commons.wikimedia.org/wiki/File:Amar_Singh_Gate,_Agra_Fort,_Agra.jpg) | Kmohankar | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | 858369 |
| `agra_fort` | `ref_05.jpg` | [File:Jahangir Mahal - Front View - Agra Fort.jpg](https://commons.wikimedia.org/wiki/File:Jahangir_Mahal_-_Front_View_-_Agra_Fort.jpg) | Arun Thundyill Saseendran | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) | 428389 |
| `agra_fort` | `ref_06.jpg` | [File:Agra Fort from its eastern flank.JPG](https://commons.wikimedia.org/wiki/File:Agra_Fort_from_its_eastern_flank.JPG) | Hadez47 (Ashwani Kumar) | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) | 374629 |
| `agra_fort` | `ref_07.jpg` | [File:Diwan-i-Khas in Agra Fort.jpg](https://commons.wikimedia.org/wiki/File:Diwan-i-Khas_in_Agra_Fort.jpg) | Rohit Sharma | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | 531642 |
| `elephanta_caves` | `ref_04.jpg` | [File:Cave No-2 of Elephenta Caves.jpg](https://commons.wikimedia.org/wiki/File:Cave_No-2_of_Elephenta_Caves.jpg) | Vaikoovery | [CC BY 3.0](https://creativecommons.org/licenses/by/3.0) | 1083734 |
| `elephanta_caves` | `ref_05.jpg` | [File:Elephanta Cave 3 2.jpg](https://commons.wikimedia.org/wiki/File:Elephanta_Cave_3_2.jpg) | Rangan Datta Wiki | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | 915364 |
| `elephanta_caves` | `ref_06.jpg` | [File:Elephanta Cave 1 E1.jpg](https://commons.wikimedia.org/wiki/File:Elephanta_Cave_1_E1.jpg) | Rangan Datta Wiki | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | 1883799 |
| `jama_masjid` | `ref_01.jpg` | [File:Jama Masjid, Delhi.jpg](https://commons.wikimedia.org/wiki/File:Jama_Masjid,_Delhi.jpg) | Muhammad Mahdi Karim | [GFDL 1.2](http://www.gnu.org/licenses/old-licenses/fdl-1.2.html) | 474238 |
| `jama_masjid` | `ref_02.jpg` | [File:Jama Masjid01.jpg](https://commons.wikimedia.org/wiki/File:Jama_Masjid01.jpg) | MaximusPrasad | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | 789838 |
| `jama_masjid` | `ref_03.jpg` | [File:Night view of Jama Masjid Delhi.jpg](https://commons.wikimedia.org/wiki/File:Night_view_of_Jama_Masjid_Delhi.jpg) | ShadabAkhtar0786 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | 426192 |
| `khajuraho_temples` | `ref_04.jpg` | [File:RNS Khajuraho11.jpg](https://commons.wikimedia.org/wiki/File:RNS_Khajuraho11.jpg) | Nallasellan | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | 1365148 |
| `khajuraho_temples` | `ref_05.jpg` | [File:The Vishwanath Temple, Khajuraho 01.jpg](https://commons.wikimedia.org/wiki/File:The_Vishwanath_Temple,_Khajuraho_01.jpg) | Rohit Sharma | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | 552227 |
| `khajuraho_temples` | `ref_06.jpg` | [File:Chitragupta temple belonging to Western Group of Temples at Khajuraho in Madhya Pradesh.jpg](https://commons.wikimedia.org/wiki/File:Chitragupta_temple_belonging_to_Western_Group_of_Temples_at_Khajuraho_in_Madhya_Pradesh.jpg) | Amitabha Gupta | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | 704759 |
| `red_fort` | `ref_04.jpg` | [File:Lahori Gate, Red Fort, Delhi.jpg](https://commons.wikimedia.org/wiki/File:Lahori_Gate,_Red_Fort,_Delhi.jpg) | Ranjeet Chauhan | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | 832236 |
| `red_fort` | `ref_05.jpg` | [File:Lahori Gate, Red Fort, Delhi - Lit up at night.jpg](https://commons.wikimedia.org/wiki/File:Lahori_Gate,_Red_Fort,_Delhi_-_Lit_up_at_night.jpg) | Ronakshah1990 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | 695595 |
| `red_fort` | `ref_06.jpg` | [File:Red Fort Arch and Towers.jpg](https://commons.wikimedia.org/wiki/File:Red_Fort_Arch_and_Towers.jpg) | Pallav.journo | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | 351267 |
| `red_fort` | `ref_07.jpg` | [File:20191203 Diwan-i-Khas, Red Fort, Delhi 0503 6358 DxO.jpg](https://commons.wikimedia.org/wiki/File:20191203_Diwan-i-Khas,_Red_Fort,_Delhi_0503_6358_DxO.jpg) | Jakub Hałun | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | 569130 |

## Notes

- Jama Masjid photos (2012 front exterior, 2016 exterior, 2022 night view) and
  the Khajuraho / Elephanta photos are the verified files from the project
  expansion pack; Red Fort and Agra Fort photos were selected from Commons
  search results on 15 November 2026 for varied angles (gates, ramparts,
  palace fronts, interiors). One near-duplicate Jahangir Mahal frontal was
  downloaded, inspected, and deliberately NOT included.
- The pre-existing `reference_gallery_100` photos (477 files) were already in
  the repository via Git LFS; their provenance is unchanged by this fix pass.
