#Requires Autohotkey v2.0-
/**
 * =========================================================================== *
 * @author      RaptorX                                                        *
 * @version     0.3.1                                                          *
 * @copyright   Copyright (c) 2024 RaptorX                                     *
 * @devPath     S:\lib\v2\ScriptObject\ScriptObject.ahk					       *
 * @link        https://www.isaiasbaez.com                                     *
 * @created     2022-07-13                                                     *
 * @modified    2024-12-12                                                     *
 * @description                                                                *
 * --------------------------------------------------------------------------- *
 * Small library to add similar functionality to all scripts                   *
 * =========================================================================== *
 * @license     GPLv3                                                          *
 * =========================================================================== *
 * License:                                                                    *
 * Copyright ©2022 RaptorX <GPLv3>                                             *
 *                                                                             *
 * This program is free software: you can redistribute it and/or modify        *
 * it under the terms of the **GNU General Public License** as published by    *
 * the Free Software Foundation, either version 3 of the License, or           *
 * (at your option) any later version.                                         *
 *                                                                             *
 * This program is distributed in the hope that it will be useful,             *
 * but **WITHOUT ANY WARRANTY**; without even the implied warranty of          *
 * **MERCHANTABILITY** or **FITNESS FOR A PARTICULAR PURPOSE**.  See the       *
 * **GNU General Public License** for more details.                            *
 *                                                                             *
 * You should have received a copy of the **GNU General Public License**       *
 * along with this program. If not, see:                                       *
 * <http://www.gnu.org/licenses/gpl-3.0.txt>                                   *
 * =========================================================================== *
 */

/**
 * Class: ScriptObj
 *
 * Small library to add similar functionality to all scripts
 *
 * --- ahk
script := {
	        base : ScriptObj(),
	      author : '',
	       email : '',
	     crtdate : '',
	     moddate : '',
	homepagetext : '',
	homepagelink : '',
	  donateLink : 'https://www.paypal.com/donate?hosted_button_id=MBT5HSD9G94N6',
}
 * ---
 */
class ScriptObj {
	static testing := true

	static eddID     := 0
	static systemID  := ''
	static license   := ''
	static graceDays := 0
	static iconFile  := ''   ; optional branding icon for GetLicense(); auto-detected when empty

	name {
		get => A_ScriptName
		set {
			throw MemberError('This property is read only', A_ThisFunc, 'Name')
		}
	}

	version {
		get {
			if this.HasOwnProp('_version')
				return this._version

			switch A_IsCompiled
			{
			case true:
				return RegexReplace(FileGetVersion(A_ScriptFullPath), '\.\d+$') ; convert to SemVer
			case false:
				loop read A_ScriptFullPath
				{
					if A_Index > 150
						break
					if RegExMatch(A_LoopReadLine, 'i)(?:@|Set)version\s*(?<version>[\w.-]+?)(:?\s|$)', &matched)
						return matched.version
				}

				return '0.0.0'
			}
		}
		set => this._version := Value
	}

	author       := ''
	homepagetext := ''
	homepagelink := ''
	donateLink   := ''
	email        := ''

	/**
	Function: Autostart(status)
	This Adds the current script to the autorun section for the current
	user.

	Parameters:
	@param {Integer} status - Autostart status, It can be either true or false.
	 */
	Autostart(status)
	{
		if status ~= '[^01]'
		|| Type(status) != 'Integer'
			throw ValueError('This property can only be true or false',
			                 A_ThisFunc, status)

		if status
		{
			RegWrite A_ScriptFullPath,
			         'REG_SZ',
			         'HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
			         A_ScriptName
		}
		else
		{
			try RegDelete 'HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
			              A_ScriptName
		}
	}

	/**
	Function: Splash
	Shows a custom image as a splash screen with a simple fading animation

	Parameters:
	@param {String}  img         - file to be displayed.
	@param {Integer} speed (opt) - how fast the fading animation will be. Higher value is faster.
	@param {Integer} pause (opt) - how long (in seconds) the image will be paused after fully displayed.
	 */
	Splash(img, speed:=10, pause:=2)
	{
		alpha := 0
		splash := Gui('-Caption +LastFound +AlwaysOnTop +Owner')
		picCtrl := splash.AddPicture('x0 y0', img)
		picCtrl.GetPos(,,&pWidth, &pHeight)
		WinSetTransparent alpha

		splash.Show('w' pWidth ' h' pHeight)

		loop 255
		{
			if (alpha >= 255)
				break
			alpha := Min(alpha + speed, 255)
			WinSetTransparent alpha
			sleep 10
		}

		; pause duration in seconds
		Sleep pause * 1000

		loop 255
		{
			if (alpha <= 0)
				break
			alpha := Max(alpha - speed, 0)
			WinSetTransparent alpha
			sleep 10
		}

		splash.Destroy()
		return
	}

	/**
	Function: Update(verFile, dwnFile)
	Checks for the current script version
	Downloads the remote version information
	Compares and automatically downloads the new script file and reloads the script.

	Parameters:
	@param {String} verFile - Version File
	          Remote version file to be validated against.
	@param {String} dwnFile - Download File
	          Script file to be downloaded and installed if a new version is found.
	          Should be a zip file that will be unzipped by the function
	@returns {Integer}

	Notes:
	The versioning file should only contain a version string and nothing else.
	The matching will be performed against a SemVer format and only the three
	major components will be taken into account.

	e.g. '1.0.0'

	For more information about SemVer and its specs click here: <https://semver.org/>
	*/
	Update(verFile, dwnFile)
	{
		if !this.version
			throw MemberError('You need to set the version property of the script.', A_ThisFunc)

		if !ScriptObj.isOnline()
			throw Error('No internet connection.', A_ThisFunc)

		; Version comparison is done externally via GetEDDVersion() + VerCompare
		; before calling Update(), so we skip it here and go straight to prompt.

		if MsgBox('A new version is available, do you want to update?', 'New Version', 'Y/N') = 'No'
			return false

		; download and install update
		InstallNewVersion(dwnFile)
		return true

		InstallNewVersion(dwnFile)
		{

			cleanName := A_Temp '\' RegExReplace(A_ScriptName, '\..*$')
			items := [tmpDir  :=cleanName,
			          zipDir  :=cleanName '\uzip',
			          lockFile:=cleanName '-lockfile',
			          zipFile :=cleanName '-update.zip']

			; cleanup
			for item in items
				if FileExist(item)
					(A_Index > 2 ?  FileDelete(item) : DirDelete(item, true))

			DirCreate tmpDir
			DirCreate zipDir

			if !InStr(zipFile, '.zip')
				throw ValueError('The file to download must be a Zip File')

			FileAppend A_Now, lockFile
			Download dwnFile, zipFile

			; Extract zip file to temporal folder
			oShell := ComObject('Shell.Application')
			oDir := oShell.NameSpace(zipDir), oZipFile := oShell.NameSpace(zipFile)
			oDir.CopyHere(oZipFile.Items)

			; { unfoldable variables
			tmpBatch :=
			(Ltrim
				':lock
				timeout /t 2
				if not exist "' lockFile '" goto continue
				goto lock
				:continue

				xcopy "' zipDir '\*.*" "' A_ScriptDir '\" /E /C /I /Q /R /K /Y
				if exist "' A_ScriptFullPath '" cmd /C "' A_ScriptFullPath '"

				cmd /C "rmdir "' tmpDir '" /S /Q"
				exit'
			)
			tmpScript :=
			(Ltrim
				'while (FileExist("' lockFile '"))
					sleep 10

				DirCopy "' zipDir '\", "' A_ScriptDir '", true

				if MsgBox("Do you want to load the new script?", "Update Successful", "Y/N") = "No"
					ExitApp

				if (FileExist("' A_ScriptFullPath '"))
					Run "' A_ScriptFullPath '"
				else
					MsgBox "There was an error while running the updated version.``n"
					. "Try to run the program manually.",
					"Update Error",
					0x10 + 0x1000
				ExitApp'
			)
			; }

			FileAppend A_IsCompiled ? tmpBatch : tmpScript, tmpDir "\update.bat"

			if A_IsCompiled
				Run A_ComSpec ' /c "' tmpDir '\update.bat"',, "Hide"
			else
				Run '"' A_AhkPath '" "' tmpDir '\update.bat"'

			await := A_ScriptFullPath
			delfile := A_Temp '\' . A_ScriptName . '.old'

			FileDelete lockFile

			FileMove await, delfile, 1

			while !FileExist(await)
				sleep 600

			if !ScriptObj.testing
				ExitApp
		}
	}

	/**
	 *
	 * @param {String} verFile
	 * @returns {Array}
	 */
	static GetUpcomingVersion(verFile)
	{
		verFile := !(verFile ~= '^https?:\/\/') ? 'https://' verFile : verFile
		http := ComObject('WinHttp.WinHttpRequest.5.1')
		http.Open('GET', verFile, true)
		http.Send()
		if !http.WaitForResponse(10)
			throw Error('Version check timed out.', A_ThisFunc, verFile)

		return StrSplit(Trim(http.responseText), '.')
	}

	/**
	 *
	 * @param {Array} current  - SemVer parts as Array, e.g. ['1', '2', '0']
	 * @param {Array} upcoming - SemVer parts as Array, e.g. ['1', '3', '0']
	 * @returns {Integer}
	 */
	static isNewVersionAvailable(current, upcoming)
	{
		if Type(current) != 'Array'
		|| Type(upcoming) != 'Array'
			throw ValueError('Invalid value. Both parameters must be Arrays.',
					A_ThisFunc, 'current: ' Type(current) ' / upcoming: ' Type(upcoming))

		loop 3
		{
			c := Integer(current[A_Index])
			u := Integer(upcoming[A_Index])
			if (u > c)
				return true
			if (u < c)
				return false
		}
		return false
	}

	/**
		Function: About
		Shows a quick HTML Window based on the object's variable information

		Parameters:
		scriptName   (opt) - Name of the script which will be
		                     shown as the title of the window and the main header
		version      (opt) - Script Version in SimVer format, a "v"
		                     will be added automatically to this value
		author       (opt) - Name of the author of the script
		homepagetext (opt) - Display text for the script website
		homepagelink (opt) - Href link to that points to the scripts
		                     website (for pretty links and utm campaing codes)
		donateLink   (opt) - Link to a donation site
		email        (opt) - Developer email

		Notes:
		The function will try to infer the paramters if they are blank by checking
		the class variables if provided. This allows you to set all information once
		when instatiating the class, and the about GUI will be filled out automatically.
	*/

	/**
	 *
	 * @param {String} scriptName
	 * @param {String} version
	 * @param {String} author
	 * @param {String} homepagetext
	 * @param {String} homepagelink
	 * @param {String} donateLink
	 * @param {String} email
	 */
	About(scriptName?, version?, author?, homepagetext?, homepagelink?, donateLink?, email?)
	{
		static doc := ''

		scriptName := scriptName ?? this.name
		version := version ?? this.version
		author := author ?? this.author
		homepagetext := homepagetext ?? RegExReplace(this.homepagetext, "http(s)?:\/\/")
		homepagelink := homepagelink ?? RegExReplace(this.homepagelink, "http(s)?:\/\/")
		donateLink := donateLink ?? RegExReplace(this.donateLink, "http(s)?:\/\/")
		email := email ?? this.email

		if (donateLink)
		{
			donateSection :=
			(
				'<div class="donate">
					<p>If you like this tool please consider <a href="https://' donateLink '">donating</a>.</p>
				</div>
				<hr>'
			)
		}
		else
			donateSection := ''

		html :=
		(
			'<!DOCTYPE html>
			<html lang="en" dir="ltr">
				<head>
					<meta charset="utf-8">
					<meta http-equiv="X-UA-Compatible" content="IE=edge">
					<style media="screen">
						.top {
							text-align:center;
						}
						.top h2 {
							color:#2274A5;
							margin-bottom: 5px;
						}
						.donate {
							color:#E83F6F;
							text-align:center;
							font-weight:bold;
							font-size:small;
							margin: 20px;
						}
						p {
							margin: 0px;
						}
					</style>
				</head>
				<body>
					<div class="top">
						<h2>' scriptName '</h2>
						<p>v' version '</p>
						<hr>
						<p>' author '</p>
						<p><a href="https://' homepagelink '" target="_blank">' homepagetext '</a></p>
					</div>
					' donateSection '
				</body>
			</html>'
		)

		btnxPos := 300/2 - 75/2
		axHight := donateLink ? 16 : 12

		aboutScript := Gui('+AlwaysOnTop +ToolWindow', "About " this.name)
		aboutScript.MarginX := 0
		aboutScript.BackColor := 'white'
		doc := aboutScript.AddActiveX('w300 r' axHight, 'HTMLFile').value
		aboutScript.AddButton('w75 x' btnxPos, "Close").OnEvent('Click', (*)=>aboutScript.Destroy())
		doc.Write(html)
		doc.Close()
		aboutScript.Show()
	}

	static GetLicense()
	{
		static cleanName := RegexReplace(A_ScriptName, '\..*$')
		static errMsg := 'It looks like ' cleanName ' is not licensed on this computer yet.`n`n'
		               . 'Do you have a license code you would like to activate now?'

		ScriptObj.systemID := ScriptObj.GetSystemID()
		if (lic_number := RegRead('HKCU\SOFTWARE\' cleanName, 'lic_number', false))
		&& ScriptObj.IsLicenceValid(lic_number)
			return ScriptObj.license := lic_number

		if Msgbox(errMsg, cleanName ' - License Required', 'IconX Y/N') = 'No'
			ScriptObj.Cancel(cleanName ' cannot run without a valid license.', cleanName ' - Unable to Run')

		license := Gui('-MinimizeBox -MaximizeBox +AlwaysOnTop', cleanName ' - License Activation')
		license.BackColor := 'FFFFFF'
		license.MarginX := 20, license.MarginY := 20
		license.SetFont('s10', 'Segoe UI')
		license.OnEvent('Close',  (*)=> Bail())
		license.OnEvent('Escape', (*)=> Bail())

		; --- Header: app icon + title -------------------------------------------
		; Resolve a branding icon: explicit ScriptObj.iconFile → compiled exe icon
		; → res\<name>.ico → <name>.ico next to the script. AddPicture is wrapped in
		; try, so a miss just renders the dialog without an icon.
		iconSrc := ''
		if (ScriptObj.iconFile != '' && FileExist(ScriptObj.iconFile))
			iconSrc := ScriptObj.iconFile
		else if A_IsCompiled
			iconSrc := A_ScriptFullPath
		else if FileExist(A_ScriptDir '\res\' cleanName '.ico')
			iconSrc := A_ScriptDir '\res\' cleanName '.ico'
		else if FileExist(A_ScriptDir '\' cleanName '.ico')
			iconSrc := A_ScriptDir '\' cleanName '.ico'
		if (iconSrc != '')
			try license.AddPicture('x20 y20 w36 h36', iconSrc)
		license.SetFont('s13 Bold c1F2937', 'Segoe UI')
		license.AddText('x64 y20 w312', cleanName)
		license.SetFont('s10 Norm c6B7280', 'Segoe UI')
		license.AddText('x64 y+2 w312', 'License Activation')

		; --- Instruction + input ------------------------------------------------
		license.SetFont('s10 c1F2937', 'Segoe UI')
		license.AddText('xm y+22 w356', 'Enter the license code you received with your purchase of ' cleanName ' to activate this computer.')
		license.AddText('xm y+16 w356', 'License code:')
		license.AddEdit('xm y+4 w356 h26 vLicenseNumber')

		; --- Buttons (right-aligned, Activate is the default) -------------------
		license.AddButton('x206 y+18 w80 h30 Default', 'Activate').OnEvent('Click', Save)
		license.AddButton('x+10 yp w80 h30', 'Cancel').OnEvent('Click', (*)=> Bail())
		license.Show()
		WinWaitClose license
		return

		; The license window is +AlwaysOnTop, so any MsgBox shown while it is
		; visible renders *behind* it. Every exit/success path hides the window
		; first, leaving the dialog as the only top-level window — guaranteed
		; visible and focused.
		Bail()
		{
			license.Hide()
			ScriptObj.Cancel(cleanName ' cannot run without a valid license.', cleanName ' - Unable to Run')
		}

		Save(*)
		{
			LicenseNumber := Trim(license['LicenseNumber'].value)
			if ScriptObj.IsLicenceValid(LicenseNumber)
			{
				SaveLicense(LicenseNumber)
				license.Hide()                       ; clear topmost before the success dialog
				MsgBox 'The license was applied correctly!`n'
				     . cleanName ' will start now.',
				       cleanName ' - License Activated', 'Iconi'
				Reload
			}
			else
			{
				license.Hide()
				ScriptObj.Cancel('The license you entered is invalid and cannot be activated.', cleanName ' - Invalid License')
			}
		}

		SaveLicense(LicenseNumber)
		{
			key := 'HKCU\SOFTWARE\' RegexReplace(A_ScriptName, '\..*$')
			RegWrite ScriptObj.license := LicenseNumber, 'REG_SZ', key, 'lic_number'
		}
	}

	/**
	 * Checks internet connectivity with a 5-second timeout.
	 * @returns {Integer} - true if online, false otherwise
	 */
	static isOnline()
	{
		try {
			http := ComObject('WinHttp.WinHttpRequest.5.1')
			http.Open('HEAD', 'http://www.msftconnecttest.com/connecttest.txt', false) ; HEAD is faster, no response body needed
			http.SetTimeouts(5000, 5000, 5000, 10000) ; resolve, connect, send, receive (ms)
			http.Send()
			return (http.Status >= 200 && http.Status < 500) ; any server response means we're online
		} catch {
			return false
		}
	}

	/**
	 * Validates license with rolling-grace offline tolerance.
	 *
	 * Behavior:
	 *   - Within ScriptObj.graceDays of last successful check: script starts
	 *     immediately. A background SetTimer silently re-validates (via
	 *     IsLicenceValid on the stored lic_number). On success, the
	 *     last_license_check timestamp is pushed forward — rolling window.
	 *   - Past graceDays (or never validated): online validation is REQUIRED.
	 *     If offline, MsgBox + ExitApp. If online, run GetLicense() (interactive
	 *     license-entry GUI if needed), then write timestamp.
	 *
	 * Net effect: every startup tries to refresh the grace window, but only
	 * blocks startup when the grace window has fully expired AND the network
	 * is unreachable. Background path uses IsLicenceValid (silent), never
	 * GetLicense (which can pop the license-entry GUI mid-use).
	 */
	static CheckOfflineLicense()
	{
		static cleanName := RegexReplace(A_ScriptName, '\..*$')
		key := 'HKCU\SOFTWARE\' cleanName

		last_check := RegRead(key, 'last_license_check', 0)
		daysSince  := last_check ? DateDiff(A_Now, last_check, 'Days') : 99999

		if daysSince > ScriptObj.graceDays
		{
			if !ScriptObj.isOnline()
			{
				MsgBox('Please connect to the internet to validate your license.',
				       cleanName ' - License Check Required', 'IconX')
				ExitApp
			}
			ScriptObj.GetLicense()
			RegWrite(A_Now, 'REG_SZ', key, 'last_license_check')
			return
		}

		; Within grace — don't block startup; revalidate in background.
		; -5000 delay gives consumer GUI time to fully render before timer fires.
		SetTimer(BgValidate, -5000)
		return

		BgValidate()
		{
			lic := RegRead(key, 'lic_number', '')
			if !lic
				return
			; The EDD check_license call needs this machine's id in its url.
			; GetLicense() normally sets systemID, but this background path
			; runs without it — so set it here or the request goes out empty
			; and validates unreliably.
			if !ScriptObj.systemID
				ScriptObj.systemID := ScriptObj.GetSystemID()
			; Skip isOnline() probe — let IsLicenceValid's own HTTP timeout
			; handle offline. A network/timeout error throws; we catch it and
			; keep running (we only act on a definite valid/invalid answer,
			; never on an unreachable server).
			try {
				valid := ScriptObj.IsLicenceValid(lic)
			} catch {
				return                       ; Server unreachable — stay running, re-check next launch
			}
			if valid
				RegWrite(A_Now, 'REG_SZ', key, 'last_license_check')
			else
				ScriptObj.GetLicense()       ; Definitely invalid — pop the entry GUI so the user can fix it
		}
	}

	static Cancel(msg, title) => ExitApp(!!MsgBox(msg, title, 'IconX'))

	/**
	 *
	 * @param {String} license
	 * @returns {String | Integer}
	 */
	static IsLicenceValid(license)
	{
		res := ScriptObj.EDDRequest('check_license', ScriptObj.eddID, license)

		if (InStr(res, '"license":"inactive"')
		|| InStr(res, '"license":"site_inactive"'))
		&& !InStr(res, '"activations_left":0')
			res := ScriptObj.EDDRequest('activate_license', ScriptObj.eddID, license)
		; Activation limit reached for THIS code. Return not-valid (rather than
		; exiting) so the caller pops the license-entry GUI and the user can try
		; a different code instead of hitting a dead-end. Returning here also
		; avoids re-entrancy, since GetLicense() calls this same function.
		else if InStr(res, '"activations_left":0')
			return false

		return InStr(res, '"license":"valid"')
	}

	/**
	 *
	 * @param {String} Action
	 * @param {String} item_id
	 * @param {String} license
	 */
	static EDDRequest(Action, item_id, license)
	{
		static url_template := 'https://the-Automator.com/?edd_action={1}&item_id={2}&license={3}&url={4}'
		URL := Format(url_template, Action, item_id, license, this.systemID)

		http := ComObject('WinHttp.WinHttpRequest.5.1')
		http.Open('GET', URL, true)
		http.SetRequestHeader('Pragma', 'no-cache')
		http.SetRequestHeader('Cache-Control', 'no-cache, no-store')
		http.SetRequestHeader('User-Agent', 'Mozilla/5.0 (compatible; Win32)')

		http.Send()
		if !http.WaitForResponse(10)
			throw Error('EDD request timed out.', A_ThisFunc, Action)
		return http.responseText
	}

	static GetEDDVersion() => ScriptObj.EDDRequest('get_version', ScriptObj.eddID, ScriptObj.license)

	static GetSystemID()
	{
		wmi := ComObjGet('winmgmts:{impersonationLevel=impersonate}!\\' A_ComputerName '\root\cimv2')
		(wmi.ExecQuery('Select * from Win32_BaseBoard')._newEnum)(&Computer)
		id := Computer.SerialNumber

		SetRegView 64
		id .= ' ' RegRead('HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion', 'ProductId')
		return MD5(id)

		MD5(str, uppercase:=true) ; by SKAN | rewritten by jNizM
		{
			static MD5_DIGEST_LENGTH := 16
			hModule := DllCall('LoadLibrary', 'Str', 'advapi32.dll', 'Ptr')

			MD5_CTX := Buffer(104, 0)
			DllCall('advapi32\MD5Init', 'Ptr', MD5_CTX)
			DllCall('advapi32\MD5Update', 'Ptr', MD5_CTX, 'AStr', str, 'UInt', StrLen(str))
			DllCall('advapi32\MD5Final', 'Ptr', MD5_CTX)
			DllCall('FreeLibrary', 'Ptr', hModule)
			o := ''
			loop MD5_DIGEST_LENGTH
				o .= Format('{:02' (uppercase ? 'X' : 'x') '}', NumGet(MD5_CTX, 87 + A_Index, 'UChar'))

			return o
		}
	}
}