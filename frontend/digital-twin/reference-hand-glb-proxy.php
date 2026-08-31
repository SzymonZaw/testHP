<?php
/**
 * Same-origin proxy for the public NIH 3D reference hand asset.
 * Only the exact allow-listed NIH asset may be fetched.
 */
declare(strict_types=1);

const NIH_GLB_URL = 'https://3d.nih.gov/api/submissions/23310/runs/c054b0b1-404c-4f43-b6a7-ddff98215e52/output-files/511811';

header('Cache-Control: public, max-age=3600');
header('X-Content-Type-Options: nosniff');

$url = isset($_GET['url']) ? (string) $_GET['url'] : '';
if ($url !== NIH_GLB_URL) {
    http_response_code(400);
    header('Content-Type: text/plain; charset=utf-8');
    echo 'Only the configured public NIH reference asset is allowed.';
    exit;
}

if (!function_exists('curl_init')) {
    http_response_code(503);
    header('Content-Type: text/plain; charset=utf-8');
    echo 'PHP cURL extension is required for the reference asset proxy.';
    exit;
}

$ch = curl_init(NIH_GLB_URL);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_FOLLOWLOCATION => true,
    CURLOPT_MAXREDIRS => 3,
    CURLOPT_CONNECTTIMEOUT => 10,
    CURLOPT_TIMEOUT => 60,
    CURLOPT_USERAGENT => 'testHP-reference-hand/1.0',
    CURLOPT_HTTPHEADER => ['Accept: model/gltf-binary, application/octet-stream, */*'],
]);

$body = curl_exec($ch);
$status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
$contentType = (string) curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
$error = curl_error($ch);
curl_close($ch);

if ($body === false || $status < 200 || $status >= 300 || $body === '') {
    http_response_code(502);
    header('Content-Type: text/plain; charset=utf-8');
    echo 'The public NIH reference asset could not be fetched.';
    if ($error !== '') {
        error_log('Reference hand proxy: ' . $error);
    }
    exit;
}

header('Content-Type: ' . ($contentType !== '' ? $contentType : 'model/gltf-binary'));
header('Content-Length: ' . strlen($body));
echo $body;
