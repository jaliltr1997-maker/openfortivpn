Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName PresentationCore

[xml]$xaml = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        Title="OpenFortiVPN" Height="380" Width="620"
        WindowStartupLocation="CenterScreen" ResizeMode="CanMinimize"
        Background="#FF111827" Foreground="#FFE5E7EB" FontFamily="Segoe UI">
  <Grid Margin="20">
    <Grid.RowDefinitions>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="*"/>
    </Grid.RowDefinitions>

    <TextBlock Text="OpenFortiVPN" FontSize="26" FontWeight="SemiBold" Margin="0,0,0,14"/>

    <TextBox x:Name="ConfigPath" Grid.Row="1" Height="34" Padding="10,6" Text="C:\\openfortivpn\\config.ini" Background="#FF1F2937" BorderBrush="#FF374151"/>

    <StackPanel Grid.Row="2" Orientation="Horizontal" Margin="0,12,0,12">
      <Button x:Name="ConnectButton" Content="Connect" Width="120" Height="34" Margin="0,0,12,0" Background="#FF2563EB" BorderBrush="#FF1D4ED8"/>
      <Button x:Name="DisconnectButton" Content="Disconnect" Width="120" Height="34" Background="#FF374151" BorderBrush="#FF4B5563"/>
      <TextBlock x:Name="StatusText" Text="Idle" VerticalAlignment="Center" Margin="16,0,0,0"/>
    </StackPanel>

    <TextBlock Grid.Row="3" Text="Activity" FontWeight="SemiBold" Margin="0,0,0,8"/>
    <TextBox x:Name="LogBox" Grid.Row="4" IsReadOnly="True" VerticalScrollBarVisibility="Auto" TextWrapping="Wrap" Background="#FF0F172A" BorderBrush="#FF1F2937"/>
  </Grid>
</Window>
"@

$reader = (New-Object System.Xml.XmlNodeReader $xaml)
$window = [Windows.Markup.XamlReader]::Load($reader)
$configPath = $window.FindName("ConfigPath")
$connectButton = $window.FindName("ConnectButton")
$disconnectButton = $window.FindName("DisconnectButton")
$statusText = $window.FindName("StatusText")
$logBox = $window.FindName("LogBox")

$script:vpnProcess = $null

function Append-Log([string]$line) {
  $logBox.AppendText("$line`r`n")
  $logBox.ScrollToEnd()
}

$connectButton.Add_Click({
  if ($script:vpnProcess -and -not $script:vpnProcess.HasExited) {
    Append-Log "Already connected."
    return
  }

  $binary = Get-Command openfortivpn -ErrorAction SilentlyContinue
  if (-not $binary) {
    $statusText.Text = "Missing binary"
    Append-Log "openfortivpn executable was not found in PATH."
    Append-Log "Install openfortivpn in WSL/MSYS2 and provide a wrapper in PATH."
    return
  }

  $statusText.Text = "Connecting..."
  Append-Log "Starting: openfortivpn -c $($configPath.Text)"

  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $binary.Source
  $psi.Arguments = "-c `"$($configPath.Text)`""
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  $psi.CreateNoWindow = $true

  $script:vpnProcess = New-Object System.Diagnostics.Process
  $script:vpnProcess.StartInfo = $psi
  $script:vpnProcess.EnableRaisingEvents = $true

  $outputHandler = [System.Diagnostics.DataReceivedEventHandler]{
    param($sender, $args)
    if ($args.Data) { $window.Dispatcher.Invoke([action]{ Append-Log $args.Data }) }
  }

  $script:vpnProcess.add_OutputDataReceived($outputHandler)
  $script:vpnProcess.add_ErrorDataReceived($outputHandler)
  $script:vpnProcess.add_Exited({
    $window.Dispatcher.Invoke([action]{
      $statusText.Text = "Disconnected"
      Append-Log "VPN process exited."
    })
  })

  [void]$script:vpnProcess.Start()
  $script:vpnProcess.BeginOutputReadLine()
  $script:vpnProcess.BeginErrorReadLine()
  $statusText.Text = "Connected"
})

$disconnectButton.Add_Click({
  if ($script:vpnProcess -and -not $script:vpnProcess.HasExited) {
    $script:vpnProcess.Kill()
    $statusText.Text = "Disconnecting..."
    Append-Log "Disconnect requested by user."
  } else {
    Append-Log "No active connection."
  }
})

$window.ShowDialog() | Out-Null
