/**
 *  健康检查接口
 */
export async function checkBackendHealth(): Promise<boolean> {
  const response = await fetch('/health', {
    cache: 'no-store',
    signal: AbortSignal.timeout(5000),
  })

  return response.ok
}