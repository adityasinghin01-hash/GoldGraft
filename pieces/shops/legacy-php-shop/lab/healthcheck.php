<?php
declare(strict_types=1);
$context = stream_context_create(['http' => ['timeout' => 2]]);
$data = @file_get_contents('http://127.0.0.1:8080/__lab/health', false, $context);
$body = json_decode($data ?: '', true);
exit(is_array($body) && ($body['mode'] ?? '') === 'offline-lab' &&
     ($body['payments'] ?? '') === 'disabled' && extension_loaded('curl') ? 0 : 1);
