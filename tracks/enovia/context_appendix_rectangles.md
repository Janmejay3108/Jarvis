# Rectangle and offset appendix

Use this appendix only after a failure screenshot shows the target is visible, or when changing a rectangle, normalized screen portion, or anchor-relative offset. Read `context.md` first. `[verified 2026-07-30]`

## Coordinate rules

- Fixed rectangles use `[x1,y1,x2,y2]` or `(x1,y1,x2,y2)` against the connected SUT screen. The shared configuration is built around `1920 x 1080`; `common.checkSUTconnected` rejects another remote size. `[verified 2026-07-30]`
- Normalized portions use `[[x1Ratio,y1Ratio],[x2Ratio,y2Ratio]]` and are multiplied by `the remoteScreenSize`; do not replace them with absolute pixels without checking every caller. `[verified 2026-07-30]`
- Four-number values can also be offsets added to a found image/text rectangle. A negative or large value is not automatically invalid; first identify whether the consumer treats it as an absolute rectangle, point offset, or rectangle delta. `[verified 2026-07-30]`
- `set the SearchRectangle` changes Eggplant search state. Prefer an explicit `searchRectangle:` argument and clear inherited global state before assuming the named config value controlled a failure. `[verified 2026-07-30]`
- `ConfigEnovia.searchRectangles` is not the only source. Current code has 42 local `getSearchRect`, `ScreenPart`, or `commonScreenPart` declarations across shared and feature scripts. `[verified 2026-07-30]`

## Before editing coordinates

1. Record the target bounding box from the failure screenshot and the exact rectangle value received at the failing call site. `[live-run: TESTAUTOMA-7947]`
2. Resolve the provider explicitly: `config`, `ConfigEnovia`, `PartMaster.getSearchRect`, `SearchResults.getSearchRect`, or another script-local function. `[verified 2026-07-30]`
3. Check whether the value is absolute, normalized, or anchor-relative, then enumerate all consumers of the exact property/function key. `[verified 2026-07-30]`
4. Compare a passing sibling that reaches the same UI state. Preserve the smallest proven rectangle and the post-action business assertion. `[live-run: TESTAUTOMA-7947]`
5. Treat edits to central rectangles as Risk 2: validate representative callers from different suites or behavior branches. `[verified 2026-07-30]`

## High-risk rectangle map

| Qualified value | Current value | Why it matters | Evidence |
|---|---:|---|---|
| `config().SUT.leftHalf` | `[-25,-10,960,1035]` | Stops at x=960. It is unsuitable for content known to render farther right, but a later Part Master pass found its target at x=696; never label it wrong without the failing screenshot/call. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-7947]` |
| `PartMaster.getSearchRect(validationErrorArea)` | `[45,139,1706,805]` | Current import handler uses it for the Import control, and current 6170 passes it for post-import validation; it is suite-local, not a `ConfigEnovia` key. | `[verified 2026-07-30]` |
| `configEnovia().searchRectangles.createNewMEP` | `(1569,136,1917,1041)` | Narrow right-side panel used by current `Part Name` presence/disappearance checks. Full panel titles can elide, so expanding this rectangle is not the primary fix for title mismatch. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8943]` |
| `configEnovia().searchRectangles.popUpWarning` | `(709,6,1212,300)` | Default for in-page warnings and native-alert text detection; widening it changes many alert consumers. | `[verified 2026-07-30]` |
| `configEnovia().searchRectangles.loadingDialogue` | `[702,400,1464,773]` | Used by loading/no-result synchronization; disappearance still needs a post-load oracle. | `[verified 2026-07-30]` |
| `configEnovia().searchRectangles.caApprovalPopup` | `[563,354,1382,855]` | Carries BOM Loader success assertions; absence of success text can reflect upstream data/product errors. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8814]` |
| `configEnovia().searchRectangles.pageHead` | `[226,160,1910,238]` | Default `clickHome` expectation area; callers may override it for customized Home pages. | `[verified 2026-07-30]` |
| `configEnovia().searchRectangles.topBar` | `[8,80,1910,115]` | Shared navigation area for Home/header controls; an overlay can disable or cover it without changing coordinates. | `[verified 2026-07-30]` `[live-run: TESTAUTOMA-8814]` |
| `SearchResults.getSearchRect(searchResultsColumnArea)` | `[294,144,1920,369]` | Header discovery anchor; subsequent column rectangles are derived from a found location and can be shifted by horizontal scrolling. | `[verified 2026-07-30]` |
| `SearchResults.getSearchRect(bottomRightSearch)` | `[1295,695,1919,1042]` | Locates the horizontal-scroll control; failure can trigger settings/default-view recovery rather than prove a missing column. | `[verified 2026-07-30]` |

## Central `config()` inventory

Every value in each row is from `Enovia/Common.suite/Scripts/config.script`. `[verified 2026-07-30]`

| Group | Values | Evidence |
|---|---|---|
| `SUT` | `chrome=[0,73,1919,1035]`; `DesktopClient=[540,118,1371,796]`; `webForm=[0,73,1919,1035]` | `[verified 2026-07-30]` |
| `SUT` | `leftHalf=[-25,-10,960,1035]`; `rightHalf=[960,73,1919,1035]`; `topHalf=[-40,-10,1919,517.5]` | `[verified 2026-07-30]` |
| `SUT` | `bottomHalf=[0,517.5,1919,1035]`; `Center=[[600,300],[1300,850]]`; `browserRefresh=[0,10,260,100]` | `[verified 2026-07-30]` |
| `SUT` | `runWindow=[4,779,557,1080]`; `topLeftQuadrant=[0,0,1920/2,1080/2]`; `topRightQuadrant=[1920/2,0,1920,1080/2]` | `[verified 2026-07-30]` |
| `SUT` | `bottomLeftQuadrant=[0,1080/2,1920/2,1080]`; `horizontalMiddle=[0,368,1920,761]`; `bottomRightQuadrant=[1920/2,1080/2,1920,1080]` | `[verified 2026-07-30]` |
| `SUT` | `VerticalMiddle=[434,80,1478,997]` | `[verified 2026-07-30]` |
| `dataEntry` | `textBoxOffset=[10,25]`; `textBoxOffsetToRight=[150,5]`; `searchBoxOffset=[5,0]` | `[verified 2026-07-30]` |
| `dataEntry` | `checkBoxOffset=[-20,0]`; `DropBoxOffset=[1,30]`; `DropBoxSelectionOffset=[10,5]` | `[verified 2026-07-30]` |
| `dataEntry` | `radioBoxOffset=[-80,0]`; `textBoxOffsetToLeft=[-150,0]` | `[verified 2026-07-30]` |

## Central `configEnovia().offsets` inventory

Every value in each row is from `Enovia/EnoviaCommon.suite/Scripts/ConfigEnovia.script`. `[verified 2026-07-30]`

| Values | Evidence |
|---|---|
| `enterField=[10,0]`; `searchField=[0,0]`; `readField=[-9,6,159,32]` | `[verified 2026-07-30]` |
| `advSearchResultsPosition=[1100,400]`; `previewPagePropertiesRead=[201,-22,425,6]`; `SpecifyDetails=[110,0]` | `[verified 2026-07-30]` |
| `leftTextBox=[-50,0]`; `downAndRight=[50,100]`; `resultsTitleToSort=[6,0,0,-20]` | `[verified 2026-07-30]` |
| `resultsTypeToSort=[460,0,170,-20]`; `resultsDateToSort=[960,0,586,-20]`; `predefinedSearchResults=[-180,0,0,0]` | `[verified 2026-07-30]` |
| `predefinedTypeValidation=[260,30,-50,-10]`; `globalSearchResults=[-192,0,-200,0]`; `revisionRead=[202,-4,117,4]` | `[verified 2026-07-30]` |
| `searchResultDropdown=[70,0]`; `complianceWindow=[500,0]`; `radiobutton=[-10,0]` | `[verified 2026-07-30]` |
| `childPartRow=[-60,-8,1500,10]`; `readEBOMPart=[+50,-5,150,5]`; `readEBOMrevision=[210,0,250,0]` | `[verified 2026-07-30]` |
| `findRectangle=[-335,0,-40,0]`; `AssemblyPart=[20,-5,50,25]`; `COpartClick=[-1400,-5,-1430,10]` | `[verified 2026-07-30]` |
| `AssemblyPartRow=[-75,-15,1500,15]`; `childPart=[60,-5,165,0]`; `childRevision=[140,0,60,0]` | `[verified 2026-07-30]` |

## Central `configEnovia().searchRectangles` inventory

Every value in each row is from `Enovia/EnoviaCommon.suite/Scripts/ConfigEnovia.script`. `[verified 2026-07-30]`

| Values | Evidence |
|---|---|
| `actionNotification=[0,975,705,1035]`; `actionsMenu=(1,123,231,285)`; `addLargePopUpWindow=[481,186,1454,964]` | `[verified 2026-07-30]` |
| `addMediumPopUpWindow=[466,265,1477,838]`; `addRightPane=[1571,160,1914,1026]`; `addSmallPopUpWindow=[555,288,1380,859]` | `[verified 2026-07-30]` |
| `addTopLevelItem=[1620,80,1920,654]`; `adv6wTags=[400,121,580,469]`; `advancedSearchResultsColumn=[550,234,1003,975]` | `[verified 2026-07-30]` |
| `advancedSearchResultsWithoutHeaders=[491,227,1900,1000]`; `advSearchCreationDate=[25,779,457,869]`; `advSearchCriteriaCheck=[-20,0,100,55]` | `[verified 2026-07-30]` |
| `advSearchFirstColumn=(290,265,700,1020)`; `advSearchFirstRow=[484,229,1900,260]`; `advSearchLineNumbers=[486,206,511,958]` | `[verified 2026-07-30]` |
| `advSearchModificationDate=[24,537,456,627]`; `advSearchPageText=[473,87,851,237]`; `advSearchParts=[479,135,1919,1038]` | `[verified 2026-07-30]` |
| `advSearchResults=[1002,206,1913,979]`; `advSearchResultsCount=[480,155,1643,200]`; `basicSearchResultsWithoutHeaders=[288,276,1575,1015]` | `[verified 2026-07-30]` |
| `browserErrorPopup=[721,73,1194,280]`; `caLeftMenu=[21,231,219,1003]`; `caApprovalPopup=[563,354,1382,855]` | `[verified 2026-07-30]` |
| `createDashboardPopupWithoutTitle=[670,204,1249,640]`; `createNewMEP=(1569,136,1917,1041)`; `dashboardDropDown=[312,115,552,710]` | `[verified 2026-07-30]` |
| `downloadsWindow=(1389,11,1829,402)`; `EBOMParts=[215,212,1900,1000]`; `EBOMHeader=(209,245,1916,298)` | `[verified 2026-07-30]` |
| `EBOMLevelsColumn=(0,144,64,1002)`; `EBOMMassUpdate=(219,209,601,350)`; `EBOMNameColumn=(213,216,432,1007)` | `[verified 2026-07-30]` |
| `EBOMQtyColumn=(694,249,816,1001)`; `EBOMReportEBOM2=(550,167,896,510)`; `EBOMReportCompareCriteria=(10,106,1899,579)` | `[verified 2026-07-30]` |
| `EBOMReportCompareLabels=(5,575,991,681)`; `EBOMReportCompareOutput=(9,735,1894,1016)`; `EBOMReportColumns=(0,140,1918,192)` | `[verified 2026-07-30]` |
| `EBOMReportHeader=(3,58,715,96)`; `EBOMReportLevels=(157,199,356,228)`; `EBOMReportMenu=(609,203,827,728)` | `[verified 2026-07-30]` |
| `EBOMRevisionColumn=(446,316,517,956)`; `EBOMTools=(212,140,1537,213)`; `EBOMPartsRemove=[566,296,1374,855]` | `[verified 2026-07-30]` |
| `entireWebPage=[0,116,1912,1034]`; `equivalentsActionsMenu=(218,166,438,433)`; `insertPartDropDown=(215,170,439,430)` | `[verified 2026-07-30]` |
| `leftPane=[5,119,469,1029]`; `leftFilterList=[7,195,408,998]`; `loadingDialogue=[702,400,1464,773]` | `[verified 2026-07-30]` |
| `loginDialogue=[958,370,1358,708]`; `mainPaneWithLeftExpanded=[483,115,1915,1026]`; `manageDashboardDialog=[207,167,1708,1004]` | `[verified 2026-07-30]` |
| `menu6wTags=[3,113,1913,172]`; `notificationsWithHeaders=[2,169,1918,1040]`; `pageHead=[226,160,1910,238]` | `[verified 2026-07-30]` |
| `partLeftMenu=(11,128,216,1038)`; `popUpWarning=(709,6,1212,300)`; `powerView=[218,180,1914,1000]` | `[verified 2026-07-30]` |
| `newPowerView=[219,139,1914,1000]`; `powerViewArea=[189,136,1911,993]`; `propertiesDate=(213,300,386,337)` | `[verified 2026-07-30]` |
| `propertiesTab=(212,207,1061,1039)`; `propertiesValidation=(13,133,1344,1037)`; `RefDesColumn=(1204,258,1404,990)` | `[verified 2026-07-30]` |
| `readCO=(214,280,431,345)`; `revisionColumn=(434,213,507,986)`; `revisionSidebar=(1366,121,1919,1040)` | `[verified 2026-07-30]` |
| `revisionHeader=(86,54,214,127)`; `rightPane=[1400,115,1920,1040]`; `routePropertiesHeader=(213,134,1053,215)` | `[verified 2026-07-30]` |
| `routeStatus=(1411,252,1734,420)`; `routeTasks=(221,615,1897,1006)`; `routeWizardCreateDialogBottomActionButtons=[2,991,1914,1040]` | `[verified 2026-07-30]` |
| `routeWizardCreateDialogFieldsArea=[2,134,1914,664]`; `routeWizardCreateDialogHeaderAndMenu=[2,62,1914,136]`; `routeWizardTaskCheckbox=(2,175,103,1029)` | `[verified 2026-07-30]` |
| `routeWizardTitleHeader=(2,131,1919,179)`; `searchDate=[22,540,470,1031]`; `searchOptions=[1203,222,1615,498]` | `[verified 2026-07-30]` |
| `searchResultsColumn=[352,237,805,1028]`; `searchResultsPane=[273,173,1576,1018]`; `searchSubMenu=[1132,110,1345,453]` | `[verified 2026-07-30]` |
| `subscriptionEventColumn=(0,135,226,991)`; `subscriptionHeader=(2,53,375,135)`; `toolsPane=[214,138,1919,313]` | `[verified 2026-07-30]` |
| `topBar=[8,80,1910,115]`; `welcomeSplashScreen=[645,335,1274,832]`; `centerPane=[480,171,1473,965]` | `[verified 2026-07-30]` |
| `advSearchSubmenu=[1060,83,1320,423]`; `docSearchLeftPane=[8,113,476,1053]`; `advanceSearchInformation=[1536,203,1919,1025]` | `[verified 2026-07-30]` |
| `middleNewWindowPopUpArea=[468,271,1465,833]`; `emailArea=[630,327,1910,1031]`; `cmdResultArea=[1,2,898,1066]` | `[verified 2026-07-30]` |
| `categoriesArea=[7,129,216,1035]`; `pwdArea=[9,10,1919,595]`; `threeDSearchAppArea=[2,280,484,1071]` | `[verified 2026-07-30]` |

## High-risk local inventories

### `PartMaster.getSearchRect`

| Values | Evidence |
|---|---|
| `dashboardTabArea=[5,78,1911,183]`; `dragDashBoardArea=[946,163,1441,526]`; `ERProductArea=[311,133,1919,191]` | `[verified 2026-07-30]` |
| `validationErrorArea=[45,139,1706,805]`; `dashboardTabsArea=[117,122,1920,174]`; `engReleaseIconSR=[965,194,1912,336]` | `[verified 2026-07-30]` |

### `SearchResults.getSearchRect`

| Values | Evidence |
|---|---|
| `searchResultsColumnArea=[294,144,1920,369]`; `bottomRightSearch=[1295,695,1919,1042]`; `bottomLeftSearch=[668,700,1136,1042]` | `[verified 2026-07-30]` |
| `popUpArea=[477,234,1892,987]`; `topRightSearch=[1061,116,1919,437]`; `okCancelBtnArea=[1517,209,1919,1045]` | `[verified 2026-07-30]` |
| `newWindowPropArea=[218,137,1223,1038]`; `topResultsArea=[454,123,1889,324]`; `partProperties=[211.2,108,1115.8,1026]` | `[verified 2026-07-30]` |
| `globalSearchArea=[685,76,1365,226]`; `indexingArea=[252,202,566,302]` | `[verified 2026-07-30]` |

`SearchResults.ScreenPart` separately defines normalized areas such as `searchResultsArea` and `FullSearchResult`; calls to `ScreenPart(...)` are not calls to `getSearchRect(...)`. `[verified 2026-07-30]`

## Local provider map

Open the named declaration before using or editing a local key. A repeated key name in another script is not the same provider. `[verified 2026-07-30]`

| Suite | Scripts declaring local rectangle providers | Evidence |
|---|---|---|
| `3DDashboard.suite` | `3DDashboard.script` | `[verified 2026-07-30]` |
| `BoundaryApps.suite` | `AMSMEP.script`, `BoundaryApps.script`, `Servers.script` | `[verified 2026-07-30]` |
| `Common.suite` | `common.script` (`commonScreenPart`) | `[verified 2026-07-30]` |
| `EngineeringCentral.suite` | `ECPartPage.script` (`ScreenPart`, `getSearchRect`) | `[verified 2026-07-30]` |
| `EnoviaCommon.suite` | `CDS.script`, `CommonEnovia.script`, `CommonEnoviaContd.script`, `Email.script`, `EnoviaChangeManagement.script`, `EnoviaSearch.script`, `Firefox.script`, `LaunchApp.script`, `OracleERP.script` | `[verified 2026-07-30]` |
| `M&AFoundational.suite` | `CADDrawing.script`, `Companies.script`, `MaterialDeclaration.script`, `PartAndMEP.script` | `[verified 2026-07-30]` |
| `MACS.suite` | `MACS.script` | `[verified 2026-07-30]` |
| `MaterialsComplianceCentral.suite` | `ContactManagement.script`, `MaterialsComplianceCentral.script`, `MCCCalculateCompliance.script`, `MCCMEP.script`, `MCCReports.script` | `[verified 2026-07-30]` |
| `MSFIntegration.suite` | `MSFDocument.script`, `MSFIntegration.script`, `MSFMDR.script` | `[verified 2026-07-30]` |
| `PartMaster.suite` | `PartMaster.script`, `Routes.script` | `[verified 2026-07-30]` |
| `PLMBridge.suite` | `PUTTY.script`, `WINSCP.script` | `[verified 2026-07-30]` |
| `Search.suite` | `FavoriteSearch.script`, `SearchResults.script` (`ScreenPart`, `getSearchRect`) | `[verified 2026-07-30]` |
| `SupplierCentral.suite` | `SupplierCentral.script` (`ScreenPart`, `getSearchRect`) | `[verified 2026-07-30]` |

## Validation after an edit

- Search every executable consumer of the exact qualified key and record whether the rectangle is passed directly, added to an anchor, or installed as global search state. `[verified 2026-07-30]`
- Run at least one target-visible positive case and one target-absent/alternate-state case; a larger rectangle can create a wrong match outside the intended panel. `[verified 2026-07-30]`
- Capture the actual found coordinates and verify the downstream business assertion, not only `ImageFound=true`. `[live-run: TESTAUTOMA-7947]`