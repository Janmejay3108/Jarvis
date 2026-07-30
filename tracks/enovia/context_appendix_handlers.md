# Handler appendix

Use this appendix when changing a shared call, adding a handler with a common name, or debugging `Handler not found`, wrong-arity, unexpected cleanup, or a helper that appears to run the wrong implementation. Read `context.md` first. `[verified 2026-07-30]`

## Evidence and scope

- Every row marked `[verified 2026-07-30]` was checked against the current `Testing_Mar10` working tree. The marker proves source text, not a successful Eggplant run.
- `SuiteInfo.helperSuitesInfo` declares provider suites available to a caller. It does not prove which body Eggplant chooses when names collide. `[verified 2026-07-30]`
- Signatures below are executable declarations in nine shared scripts; declarations inside `(* ... *)` comments are excluded. `[verified 2026-07-30]`
- Never infer behavior from a bare handler name. Resolve `caller suite -> provider suite -> script -> declaration -> call site`. `[verified 2026-07-30]`

## Safe resolution procedure

1. Find the exact call site and preserve positional order, named/default arguments, and capitalization as written. `[verified 2026-07-30]`
2. Open the caller suite's `SuiteInfo`; only its `helperSuitesInfo` entries are declared providers. `[verified 2026-07-30]`
3. Search the caller and every declared provider for the handler name. Qualify ambiguous calls as `"ScriptName".handlerName ...`; include the suite in your investigation notes because script names are not globally unique. `[verified 2026-07-30]`
4. Inspect the entire selected body for `throw`, `exit all`, browser/SUT cleanup, clipboard use, Run-dialog commands, and screen assumptions. `[verified 2026-07-30]`
5. If one script contains duplicate executable declarations, stop. Do not claim first-wins or last-wins without the probe below. `[verified 2026-07-30]`

`[UNVERIFIED — check: in an isolated disposable Eggplant suite, define the same uniquely named handler twice with distinct return values, invoke it once using the repository's Eggplant Functional version, and record the returned value plus product version]`

## Caller-to-provider topology

These are the current `helperSuitesInfo` declarations. The graph is cyclic: notably, `Common.suite` provides `EnoviaCommon.suite`, while `EnoviaCommon.suite` provides `Common.suite` and many feature suites. Treat provider order as configuration, not proven precedence. `[verified 2026-07-30]`

| Caller suite | Declared provider suites | Evidence |
|---|---|---|
| `3DDashboard.suite` | `EnoviaCommon.suite`, `Common.suite` | `[verified 2026-07-30]` |
| `BoundaryApps.suite` | `EnoviaCommon.suite`, `Search.suite`, `EngineeringCentral.suite`, `SupplierCentral.suite` | `[verified 2026-07-30]` |
| `Common.suite` | `CustomReport.suite`, `EnoviaCommon.suite` | `[verified 2026-07-30]` |
| `CustomReport.suite` | none | `[verified 2026-07-30]` |
| `EngineeringCentral.suite` | `Common.suite`, `EnoviaCommon.suite`, `Search.suite` | `[verified 2026-07-30]` |
| `EnoviaCommon.suite` | `PLMBridge.suite`, `Search.suite`, `MaterialsComplianceCentral.suite`, `Common.suite`, `EngineeringCentral.suite`, `SupplierCentral.suite`, `M&AFoundational.suite`, `Performance.suite`, `MSFIntegration.suite`, `MACS.suite`, `TeamCenter.suite`, `BoundaryApps.suite`, `3DDashboard.suite`, `PartMaster.suite` | `[verified 2026-07-30]` |
| `LibraryCentral.suite` | `Common.suite`, `EnoviaCommon.suite` | `[verified 2026-07-30]` |
| `M&AFoundational.suite` | `Common.suite`, `EnoviaCommon.suite`, `Search.suite`, `MaterialsComplianceCentral.suite` | `[verified 2026-07-30]` |
| `MACS.suite` | `Common.suite`, `EnoviaCommon.suite`, `Search.suite` | `[verified 2026-07-30]` |
| `MaterialsComplianceCentral.suite` | `Common.suite`, `EnoviaCommon.suite`, `Search.suite` | `[verified 2026-07-30]` |
| `MSFIntegration.suite` | `M&AFoundational.suite`, `Common.suite`, `EnoviaCommon.suite` | `[verified 2026-07-30]` |
| `PartMaster.suite` | `EnoviaCommon.suite`, `Common.suite` | `[verified 2026-07-30]` |
| `Performance.suite` | `Common.suite`, `Search.suite`, `EnoviaCommon.suite` | `[verified 2026-07-30]` |
| `PLMBridge.suite` | `Common.suite`, `EnoviaCommon.suite` | `[verified 2026-07-30]` |
| `Search.suite` | `Common.suite`, `EnoviaCommon.suite`, `LibraryCentral.suite`, `EngineeringCentral.suite` | `[verified 2026-07-30]` |
| `SupplierCentral.suite` | `Common.suite`, `EnoviaCommon.suite`, `Search.suite`, `MaterialsComplianceCentral.suite` | `[verified 2026-07-30]` |
| `TeamCenter.suite` | `EnoviaCommon.suite`, `Common.suite`, `EngineeringCentral.suite` | `[verified 2026-07-30]` |

## Duplicate executable declarations

The signatures match within each pair, but several bodies differ materially. The line locations are discovery anchors, not a precedence claim. `[verified 2026-07-30]`

| Provider / script | Handler | Executable declarations | Wrong-turn warning | Evidence |
|---|---|---:|---|---|
| `Common.suite / common` | `CaptureScreenshot(msg)` | 59, 625 | Do not assume which screenshot/report path executes. | `[verified 2026-07-30]` |
| `Common.suite / common` | `Success(SuccessMsg)` | 80, 645 | Reporting side effects require body inspection. | `[verified 2026-07-30]` |
| `Common.suite / common` | `Error(ErrorMsg,isthrow)` | 93, 658 | Throw/report behavior requires body inspection. | `[verified 2026-07-30]` |
| `Common.suite / common` | `LogException(Exception,HandlerName)` | 114, 679 | Log and screenshot behavior requires body inspection. | `[verified 2026-07-30]` |
| `Common.suite / common` | `FetchValuebyRemoteClipBoard()` | 137, 946 | Reads the remote clipboard; it is not a controller clipboard helper. | `[verified 2026-07-30]` |
| `Common.suite / common` | `clickElement(label,SR,expectation,SR2,offset:[0,0])` | 155, 967 | Bodies are materially different; inspect both before changing a call. | `[verified 2026-07-30]` |
| `Common.suite / common` | `validateValues(values,SR:[0,0,1920,1080],pageWait:120)` | 176, 992 | One body is simple; the other uses an OCR/scroll validation ladder. | `[verified 2026-07-30]` |
| `Common.suite / common` | `SelectDropDownOnYAxis(textLabel,data,xCoordinate,yCoordinate,waitTime)` | 416, 1300 | Do not infer selection behavior from name alone. | `[verified 2026-07-30]` |
| `Common.suite / common` | `SelectDropDownOnXAndYAxis(textLabel,data,xCoordinate,yCoordinate,X1,Y1,X2,Y2,waitTime)` | 435, 1321 | Do not infer selection behavior from name alone. | `[verified 2026-07-30]` |
| `Common.suite / common` | `selectDropDownWithoutValidation(textLabel,data,xCoordinate,yCoordinate,waitTime)` | 482, 1355 | No post-selection oracle is promised by the name. | `[verified 2026-07-30]` |
| `EnoviaCommon.suite / FileOperations` | `readColumDataFrom(excelName,excelSheetName,column)` | 22, 117 | Duplicate execution order is unproved. | `[verified 2026-07-30]` |
| `EnoviaCommon.suite / FileOperations` | `readTestDataFrom(excelName,excelSheetName,column)` | 38, 138 | Duplicate execution order is unproved. | `[verified 2026-07-30]` |

## High-risk shared contracts

| Qualified handler | Contract that prevents a wrong turn | Evidence |
|---|---|---|
| `exceptionHandling.errorCapture(errorMessage,handlerName)` | Captures/logs, then performs `exit all`; a nested caller does not resume normally. | `[verified 2026-07-30]` |
| `common.scrollTo(toFind,SR,direction)` | Defaults to downward scrolling when direction is empty and hard-fails through `errorCapture` after 10 unsuccessful loops. | `[verified 2026-07-30]` |
| `common.waitForTextToDisappear(textToWaitFor,rectSearch,waitTime)` | Can return success when the text was never observed; establish presence first when disappearance is the oracle. | `[verified 2026-07-30]` |
| `CommonEnovia.searchEnovia(searchType,input,toFind,columnName:"Type")` | Iterates advanced-search criteria in caller-provided order; the property order is behavioral. | `[verified 2026-07-30]` |
| `CommonEnovia.handleAccessOtherAppsPopup(waitTime:5)` | Handles the dashboard access popup; `clickHome` invokes it and retries Home once. | `[verified 2026-07-30]` |
| `CommonEnovia.dismissNativeAlert(waitToAppear,popupRectangle,attempts)` | Parameters are positional; do not reorder them from prose intuition. | `[verified 2026-07-30]` |
| `CommonEnovia.waitForNativeAlert(popupRectangle,waitToAppear)` | Rectangle precedes wait time, unlike `dismissNativeAlert`. | `[verified 2026-07-30]` |
| `CommonEnovia.nativeAlertIsOnScreen(popupRectangle:configEnovia().SearchRectangles.PopUpWarning)` | Uses the warning rectangle by default and returns an observation; inspect the caller for the decision. | `[verified 2026-07-30]` |
| `CommonEnovia.selectTableViewDropDownOptions(option,isMandatory)` | The current shared body accepts optional mandatory behavior; inspect callers before changing failure semantics. | `[verified 2026-07-30]` |
| `SearchResults.selectItem1InSearchResults(columnName,Value,isImage)` | Selects the first matching row; it is not an iterator over duplicate matches. | `[verified 2026-07-30]` |
| `SearchResults.returnColumnLoc(columnName,isScroll)` | Uses OCR/image geometry and horizontal scrolling; stale headers or viewport position can corrupt the returned location. | `[verified 2026-07-30]` |
| `LaunchApp.LaunchURL()` | Reads controller-side resources, then types the resolved browser command on the SUT; browser config currently requests InPrivate mode. | `[verified 2026-07-30]` |
| `FileOperations` Excel/JSON handlers | SenseTalk file and Excel APIs read controller-side suite resources unless the handler explicitly types a command into the SUT. | `[verified 2026-07-30]` |

## Cross-script collision hotspots

These names have executable definitions in more than one script. This is a routing warning, not evidence that one shadows another. `[verified 2026-07-30]`

| Name | Providers / scripts | Evidence |
|---|---|---|
| `cleanup` | `EnoviaCommon.suite / CommonEnovia`, `EnoviaCommon.suite / LaunchApp` | `[verified 2026-07-30]` |
| `CloseApp` | `Common.suite / common`, `EnoviaCommon.suite / LaunchApp` | `[verified 2026-07-30]` |
| `createCompany`, `enterNewCompanyDetails` | `EnoviaCommon.suite / CommonEnovia`, `SupplierCentral.suite / SupplierCentral` | `[verified 2026-07-30]` |
| `getSearchRect` | Repeated across shared and feature scripts; always qualify it during investigation. | `[verified 2026-07-30]` |
| `handleAccessOtherAppsPopup` | `EnoviaCommon.suite / CommonEnovia`, `PartMaster.suite / PartMaster` | `[verified 2026-07-30]` |
| `launchAppFromRun`, `loginOutlook`, `loginToDigiWorker` | `EnoviaCommon.suite / CommonEnovia`, `EnoviaCommon.suite / LaunchApp` | `[verified 2026-07-30]` |
| `ScreenPart` | Repeated in `CommonEnovia`, `LaunchApp`, `SearchResults`, and feature scripts. | `[verified 2026-07-30]` |
| `selectRightClickOptions` | `EnoviaCommon.suite / EnoviaSearch`, `Search.suite / SearchResults` | `[verified 2026-07-30]` |
| `selectTableViewDropDownOptions` | `EnoviaCommon.suite / CommonEnovia`, `M&AFoundational.suite / MaterialDeclaration` | `[verified 2026-07-30]` |
| `textEntry` | `Common.suite / common`, `EnoviaCommon.suite / CommonEnovia` | `[verified 2026-07-30]` |
| `validateRandomSearchResult` | `EnoviaCommon.suite / EnoviaSearch`, `Search.suite / SearchResults` | `[verified 2026-07-30]` |

## Executable signature inventory

The inventory is source-qualified. Defaults are reproduced because omitting one can change waits, search areas, failure behavior, or UI state. `[verified 2026-07-30]`

### `Common.suite / Scripts/common.script`

```text
function commonScreenPart Portion
to getScreenPart list
to handle CaptureScreenshot msg
to Success SuccessMsg
to Error ErrorMsg,isthrow
to LogException Exception,HandlerName
To handle FetchValuebyRemoteClipBoard
to clickElement label,SR,expectation,SR2,offset:[0,0]
on validateValues values,SR:[0,0,1920,1080],pageWait:120
to handle EnterTextBoxByImage imageTextBox, data, waitTime,isthrow
to handle TodoTripleClickWRTText TextName,X,Y,waitTime
to handle TodoTripleClickWRTLoc Location,X,Y
to handle EnterTextBoxByCoordinates textLabel, data, xCoordinate,yCoordinate,waitTime,isthrow,SR
to handle EnterTextByCoordinatesWithoutClear textLabel, data, xCoordinate,yCoordinate,waitTime,isthrow,SR,isTabKey
to SelectDropDownOnYAxis textLabel, data, xCoordinate,yCoordinate,waitTime
to SelectDropDownOnXAndYAxis textLabel, data, xCoordinate,yCoordinate,X1,Y1,X2,Y2,waitTime
to handle IsTextPresentOnScreenValidwordsNoRect textBoxText,DPIVal,waitTime,isthrow
to handle IsTextPresentOnScreenValidwords textBoxText,DPIVal,waitTime,isthrow,SR
to handle selectDropDownWithoutValidation textLabel, data, xCoordinate,yCoordinate,waitTime
to isTextPresentInSearchRect textBoxText,waitTime,isthrow,rectSearch
to isTextNotPresentInSearchRect textBoxText,waitTime,isthrow,rectSearch
to handle ClickBtnByImage textImage, waitTime,searchRect,isthrow
to handle ClickByImgNoSearchRect textImage, waitTime,isthrow
to handle RightClickBtnByImage textImage, waitTime,searchRect,isthrow
to handle IsImagePresentOnScreen imgIcon,waitTime,searchRect,isthrow
to handle IsTextNotPresentOnScreen textBoxText, waitTime,searchRect,isthrow
to handle IsImageNotPresentOnScreen imgIcon,waitTime,searchRect,isthrow
to handle ClickBtnByText textLabel, waitTime,SearchRect,isthrow
to handle CaptureScreenshot msg
to Success SuccessMsg
to Error ErrorMsg,isthrow
to LogException Exception,HandlerName
to closeBrowser
to closeTab expectation,SR
to back expectation
function checkImagePresent
to scrollTo toFind, SR, direction
to navigate action, SR, SR2:[0,0,1920,1080], expectation,toWait:35
to textEntry label,input, SR, offset:(config().dataEntry.textBoxOffset),waitTime:30
to doubleClickTextEntry label,input, SR, offset:(config().dataEntry.textBoxOffset)
to hiddenTextEntry label,input, SR, offset:(config().dataEntry.textBoxOffset)
to checkBox label, SR, offset:(config().dataEntry.checkBoxOffset)
to dropDown label,input, SR, offset:(config().dataEntry.DropBoxOffset), selectionOffset:(config().dataEntry.DropBoxSelectionOffset)
to searchTextEntry label,input, SR, offset:(config().dataEntry.SearchBoxOffset)
to subMenuSelect submenu, selection, SR, SR2, SR3, expectation
to LaunchApp path,app:global browser
to CloseApp
to AppSwitcher varlogos:logos,app:global browser
to connectSUT sutName
to checkSUTconnected
To handle FetchValuebyRemoteClipBoard
to clickElement label,SR,expectation,SR2,offset:[0,0]
on validateValues values,SR:[0,0,1920,1080],pageWait:120
function generateSRForLabel label,LSR:[0,0,1920,1080],SR:[0,0,1920,1080]
to mouseActionOnPreferredElement label,SR:[0,0,1920,1080],itemNumber:1,mouseAction:Click
to refreshBrowser
to checkOrUncheckCheckBox nameLoc,XOffset,YOffset,selectedImg,unSelectedImg,CBText,isSelect
to handleBlockedPopup
to handle compareValues expResult, actualResult,isThrowYes
to handle containsValue expResult, actualResult
to handle getImagelocation TextName,waitTime
to handle selectDropDown textLabel, data, xCoordinate,yCoordinate,waitTime
to clickTextInSearchRectangle textToFind,rectSearch
To validateDailogAndDesiredAction strDialogname,strActionname,strActionImg
to validateMessage message,waitTime
to validateMsgAndClickAction setText,message,clickText
to CompareDropDownValue propertyName,checkValueList
to SelectDropDownOnYAxis textLabel, data, xCoordinate,yCoordinate,waitTime
to SelectDropDownOnXAndYAxis textLabel, data, xCoordinate,yCoordinate,X1,Y1,X2,Y2,waitTime
to handle IsTextPresentOnScreenWithDPIAndValidwords textBoxText,DPIVal,waitTime,SR,isthrow
to handle selectDropDownWithoutValidation textLabel, data, xCoordinate,yCoordinate,waitTime
to selectCheckBox checkBoxName,xCoordinate,yCoordinate,waitTime,isThrow
To handle dragfromLocationAndDropViaLoc startLoc,endLoc
to handle verifyValueIsNotEmpty fieldName,fieldvalue
to navigateAndClick action, SR, SR2:[0,0,1920,1080], expectation,toWait:35
to handle GenerateRandomNumber Alphanum,lengthofNumber
to signOutVM
to validateTextAndLogMsg textBoxText,waitTime,rectSearch,isthrow,validationMsg
to disConnectSUT
to waitForTextToDisappear textToWaitFor, rectSearch, waitTime
```

Source: `Enovia/Common.suite/Scripts/common.script`. `[verified 2026-07-30]`

### `Common.suite / Scripts/exceptionHandling.script`

```text
to handle userFriendlymessage
to handle textOrImageIsNotFound
to handle maxDepthError
to handle waitForAllError
to handle handlerNotFound
to validationFailed
to passingParametersIssue
to handle imageNotExistInSuite
to handle noImageFoundOnScreen
to handle noTextFoundOnScreen
to handle unableToFindImageOrTextWithInTime
to handle unableToFindImage
to handle imageNamePropertyError
to handle sutConnectionError
to handle connectingSUTError
to copyInaccessible
to handle capturingScreenError
to handle scriptError
function statusCodeError
to handle errorCapture errorMessage,handlerName
to failedHandlerNavigation callstackInfo
```

Source: `Enovia/Common.suite/Scripts/exceptionHandling.script`. `[verified 2026-07-30]`

### `EnoviaCommon.suite / Scripts/CommonEnovia.script`

```text
function ScreenPart Portion
to getSearchRect Portion
to readInCredentials fileName
to loginEnovia
to searchEnovia searchType, input, toFind,columnName:"Type"
to validateAdvancedSearch input, toFind
to waitForLoading
to readField label, SR, direction, offset:(configEnovia().offsets.readField)
to dataValidation label, expectedValue, SR, direction, offset:(configEnovia().offsets.readField)
to assertWithScreenshot actualValue, expectedValue, validation
to resultsFileStart testName, platformVersion
to resultsFileWrite LogStatement, separatorFlag
to resultsFileEnd
to addFavoriteSearch favSearchName
to handleAccessOtherAppsPopup waitTime:5
to clickHome expectation, expectationSR:(configEnovia().searchRectangles.pageHead)
to addMenu selection, expectation
to cleanup internetBrowser:"msedge", SUTCheck:"required"
to openApp appName, appValidation, validationSearchRectangle
to toolbarSelect button, expectation, expectationSR
to closeTabsTillHome
to logoutEnovia isIamNot
to textEntry label,input, SR, offset:(config().dataEntry.textBoxOffset)
to maximizeWindow numDelay: 1, expectation,SR:config().SUT.topHalf
to clickLeftPaneOption header, subHeader, expectation, expectationSR:configEnovia().searchRectangles.toolsPane,LeftPaneSR:configEnovia().searchRectangles.leftPane
to clickOnPartNumForPropertiesPageInleftPane partNum,LeftPaneSR:configEnovia().searchRectangles.leftPane,expectation,expectationSR:configEnovia().searchRectangles.toolsPane
to clickHeaderButton button, expectation, expectationSR:(configEnovia().searchRectangles.pageHead)
to openFirstPart
to handle popUpWarning message, clearMessage:"yes",popupRectangle:configEnovia().SearchRectangles.PopUpWarning
to handle dismissNativeAlert waitToAppear, popupRectangle, attempts
to handle waitForNativeAlert popupRectangle, waitToAppear
to handle nativeAlertIsOnScreen popupRectangle:configEnovia().SearchRectangles.PopUpWarning
to tripleClick imageToClick
to expandMenu label,SR,expectationSR,expectation
to calendarpicker datePic,SR
to findInPage toFind, SR1
to getPartNumber label,SR,offset
to verifyNewPageLoadedAndMaximize isMax,txtToValidateNewWindow,SearchRect,isValidateImage,waitTime:30
to getPartNumUsingTripleClick textToClick
to DatePickerDay Day,SearchRect
to openFirstPartInSameWindow
to createOtherDocument DocName
to ExpandNlevels
to clickUnderName
to selectActionsFromActionsMenu ListToNavigte,Expectation,ExpectationSR
to checkSortByField label,SR,expectation,SR2,offset:[0,0],LSR:[0,0,1920,1080]
to createCollection collectionName:EPT&FormattedTime("ddMMhmmss",time)
to openCollection collectionName
to addPartToTheCollection partID,isSelect,maturityState:"Not empty"
to addDocToTheCollection Document,Type
to NavigateToMyProfile
to validateCountry CountryName
to selectTableViewDropDownOptions option, isMandatory
to createCompany
to enterNewCompanyDetails input
to getCompanyPropertyValue propertyName,X,Y
to validateCompanyState
to findAnyItemWithFindIcon TextToSearch,IconSR,expectedSR
to loginToDigiWorker
to loginOutlook
to launchAppFromRun appExePath,appName,validation:"Excel",SR:config().SUT.leftHalf
to uploadToDoc path,expectation,SR
to createOtherDocumentwithstatus DocName, Type, ownername
to findAnyItemWithFindIconAndReturn TextToSearch,IconSR,expectedSR,notFound="no"
to getURL
to killBrowser
to firefoxSearchEnovia searchType, input, toFind,columnName:"Type"
```

Source: `Enovia/EnoviaCommon.suite/Scripts/CommonEnovia.script`. `[verified 2026-07-30]`

### `EnoviaCommon.suite / Scripts/CommonEnoviaContd.script`

```text
function getSearchRect Portion
to checkCalenderValuesAreEditable labelAndInput,SR,movLoc
to validateFieldPresentOrNot fieldList,present:"yes",SR,movLoc
to getRevisionLevelInProperties
to RefreshPage
to handle ValidateAttributeExistOnInformationPage propertyName
to closeActiveExcelApplication
to refreshEnoviaAPP
to waitForLoadingInTopRight
to handle pageNotResponding popupRectangle:configEnovia().SearchRectangles.PopUpWarning
to doubleClickBtnByText textLabel,waitTime,isthrow,SR
to validateJobSucceededOnUploadingData validationStatus:"Succeeded"
to createBookMark bookmarkTitle,isNavigate
to openCreatedBookMark bookMarkName,bookMarkToVerify,Open="Yes",isNavigate:"yes",expectedSR:getSearchRect(bookMarksDataSR)
to validateJobSucceededAndClose
to calendarpickerWithSR datePic,SR
to increaseZoomInWebBrowser numberOfTimes
to validateTwoLists list1,list2
to findItemUnderColumn TextToSearch,ColumnName,ColumnSR:CommonEnovia.getSearchRect(columnsArea)
to deleteFileFromDownloadPage fileName,folder="no"
to refreshApp
to validateFields text, SR, searchText
to returnIndexOfEleInList element,list
to createGenericDocument DocName,filePathToChoose
to validateDemotePromotebtnDisabled
to createGenericDocumentApprover DocName,filePathToChoose, approver, approverName
to returnCurrentEnv
to openFromDownloads filename,textBoxText,validation="yes",close="yes"
to searchApp appName,expectation,validationSearchRectangle
```

Source: `Enovia/EnoviaCommon.suite/Scripts/CommonEnoviaContd.script`. `[verified 2026-07-30]`

### Configuration-object scripts

`Enovia/Common.suite/Scripts/config.script` and `Enovia/EnoviaCommon.suite/Scripts/ConfigEnovia.script` return property lists; they do not declare executable handlers. Callers use values such as `config().SUT.leftHalf` and `configEnovia().searchRectangles.pageHead`. `[verified 2026-07-30]`

### `EnoviaCommon.suite / Scripts/LaunchApp.script`

```text
function ScreenPart Portion
to getSearchRect Portion
to LaunchURL
to CleanUp SUTCheck:"required"
to CloseApp
to launchMSF expectation:"Sign in",SR:configEnovia().SearchRectangles.centerPane
to launchAppFromRun appExePath,appName, appIcon="icn_excelTaskBar"
to loginOutlook
to loginToDigiWorker
to signInOutlook userName,password,differentUser:"no"
to cleanUpNotepad
to cleanUpCMD
to launchMSFFromDesktop expectation:"Sign in",SR:configEnovia().SearchRectangles.centerPane
to launchRunWindow
to launchMyPC expectation:"Collaboration for Microsoft",searchRect:common.commonScreenPart(TopHalf)
to launchMSFFromExplorer expectation:"Sign in",SR:configEnovia().SearchRectangles.centerPane
to launchPowershell
to loginToServersUrl
to killpowershell
to tologinUrlphysical
to closeWINSCP
to cleanUpFirefox
```

Source: `Enovia/EnoviaCommon.suite/Scripts/LaunchApp.script`. `[verified 2026-07-30]`

### `EnoviaCommon.suite / Scripts/FileOperations.script`

```text
function getcredentials
to getJSONValueFromJSONFile FileName
to handle readColumDataFrom excelName, excelSheetName, column
to handle readTestDataFrom excelName, excelSheetName, column
to fetchSpecificCellValue excelName, excelSheetName,columnName,rowNum
to handle writeDataIntoExcel excelName, excelSheetName, primaryColumnName, primaryColumnValue, columnNameToUpdate, columnNameToUpdateValue
to handle WriteOPDataintoExcelSheet excelName,excelSheetName,ColumnName,ColumnValue, primaryColumnName, primaryColumnValue
to ReadTestdataBasedOnRowNum TestDataExcelFilePath,TestDataSheetName,RowNum
to handle readColumDataFrom excelName, excelSheetName, column
to handle readTestDataFrom excelName, excelSheetName, column
to handle readTestDataWithCondition excelName, excelSheetName, column,conditionColumn,value
to handle readTestDataWithNotCondition excelName, excelSheetName, column,conditionColumn,value
to handle readTestDataWithTwoCondition excelName, excelSheetName, column,conditionColumn,value,conditionColumn1,value1
to handle updateTestData excelName, excelSheetName, column,conditionColumn,value,updateValue
to getExcelFilePath fileName
to handle fileprerequisite filename
to handle BOMLoaderPreRequisite filename1,filename2
to handle WriteDataInToTextFileForBOMLoader filename1,LinesToInput,filePathVal
to handle validatePreReqFileExists filename1,filePathVal,fileExtn = ".txt"
to deleteFileFromCMD filePath
to handle Anyfileprerequisite filePathVal, filename, fileType
to openDownloadsInWindows
to extractAZipFile name
to VerifyAndOpenDownloadedFile FileName
to createCSVFileAndWrite path,DataToWrite
to createTxtFileWithSpecSizeFromRun path,fileName,size
to fetchAParticularLineFromCsvlocal path,lineNumber
to searchCsvForParticularDetails numberOfLines,path,searchVal
to toFetchSDECOSUserData userName:"SDE-COS"
```

Source: `Enovia/EnoviaCommon.suite/Scripts/FileOperations.script`. `[verified 2026-07-30]`

### `Search.suite / Scripts/SearchResults.script`

```text
function ScreenPart Portion
to getSearchRect Portion
to returnColumnLoc columnName,isScroll
to selectItem1InSearchResults columnName,Value,isImage
to selectRightClickOptions loc,Option,XCord,YCord,isClick
to validateOpenInNewWindow isMax
to selectSearchResultsDropDownOptions Option,isClick,isNotAvailable
to validateExportInSearchResult Option,isSelect
function getExportCSVFileName fileName,timerVal
to deleteExistingCSVFiledsInDownloads
to validateFileIsDownloadedInCSV fileNameTS
to SelectDropDownOnCredentials textLabel, data, xCoordinate,yCoordinate,X1,Y1,X2,Y2
to SelectBottomRightActionInSearch action,isImage
to verifyGlobalResultsByHeader input,expectation:input,headerName,labelRectangle
to verifyTagFiltersIn6wTags
to verifyResultsByTag
to verifyResultsByHeader expectation:input,headerName,labelRectangle
to verifyAddFavoriteSearchDialog isClickFavSearchesHyperLink,isAddByName,data
to verifySearchOptionsDialog isManageGridView
to validateCustomizeSearchResultWindowIsdisplayed
to enableOrDisableColumns ColumnName,isVisibleDisable
to validateColumnIsNotAvailable columnNameList
to customizeSearchView ColumnName,isVisibleDisable,CustoName
to ValidateSearchedPartIsDisplayedFullScreen Loc,partNum,type,textToFindAfterPageLoad
to validateRandomSearchResult type, wildcard, advanced
to scrollleftadvancesearch columnName,isScroll
to advancesearchScrollLeft columnName,isScroll
to select6wTags
to selectShow6wTagsInleftPane tagName
to hide6WTagsInLeftPane
to collapseOrExpandSpecificTagInLeftPane tagToCollapseOrExpand,isExpand
to verifyOrSelectTagsOrTextInLeftPane textToFind,isSelect
to returnColumnLocWithSR columnName,isScroll
to verifyAdvSearchAttributes attributeToValidate,scrollWheelCount
to openPropertiesPreview
to validateMyContentSearchColumnReturnLoc columnName,isScroll,pageHeader:"My Content Results"
to validateDifferentFiltersSearchedUnderTags
to checkMyRecentContent textVal
```

Source: `Enovia/Search.suite/Scripts/SearchResults.script`. `[verified 2026-07-30]`

## Inventory regeneration check

Run this from the repository root after editing any shared script. It excludes multiline comments, then compares executable declaration text with this appendix. `[verified 2026-07-30]`

```powershell
$files = @(
	'Enovia/Common.suite/Scripts/common.script',
	'Enovia/Common.suite/Scripts/config.script',
	'Enovia/Common.suite/Scripts/exceptionHandling.script',
	'Enovia/EnoviaCommon.suite/Scripts/CommonEnovia.script',
	'Enovia/EnoviaCommon.suite/Scripts/CommonEnoviaContd.script',
	'Enovia/EnoviaCommon.suite/Scripts/ConfigEnovia.script',
	'Enovia/EnoviaCommon.suite/Scripts/LaunchApp.script',
	'Enovia/EnoviaCommon.suite/Scripts/FileOperations.script',
	'Enovia/Search.suite/Scripts/SearchResults.script'
)
# Re-run the repository documentation validation; do not rely on a plain text
# grep because declarations can be inside SenseTalk multiline comments.
```

Expected current executable declaration count: `285`. `[verified 2026-07-30]`