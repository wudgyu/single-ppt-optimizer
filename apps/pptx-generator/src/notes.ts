export interface SpeakerNoteInput {
  body: string;
  durationSeconds: number;
}

export function buildSpeakerNotes(input: SpeakerNoteInput): string {
  return `${input.body}\n\nSuggested duration: ${input.durationSeconds} seconds.`;
}
