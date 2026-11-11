/** Every failure the UI can show, already in the pack's words (05 §24). */
export class ApiError extends Error {
  constructor(
    public kind: 'problem' | 'timeout' | 'network' | 'unexpected',
    public status: number,
    public title: string,
    public detail?: string,
    public seconds?: number,
  ) {
    super(title);
  }
}
