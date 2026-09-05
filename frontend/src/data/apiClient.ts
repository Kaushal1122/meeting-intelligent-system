import { DashboardPayload } from '../types/meeting';

const API_BASE_URL = 'http://localhost:8000/api';

export interface HealthStatus {
  status: string;
  version: string;
  member4_active: boolean;
  message: string;
}

export interface ProcessMeetingParams {
  meetingId: string;
  audioFile?: File | null;
  transcriptFile?: File | null;
  transcriptText?: string;
  forceReprocess?: boolean;
}

export const apiClient = {
  async checkHealth(): Promise<HealthStatus> {
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      if (!res.ok) {
        throw new Error(`Health check failed: HTTP ${res.status}`);
      }
      return await res.json();
    } catch (err: any) {
      throw new Error(`Cannot reach Backend API at ${API_BASE_URL}: ${err.message}`);
    }
  },

  async processMeeting(params: ProcessMeetingParams): Promise<DashboardPayload> {
    const formData = new FormData();
    formData.append('meeting_id', params.meetingId);

    if (params.audioFile) {
      formData.append('audio', params.audioFile);
    } else if (params.transcriptFile) {
      formData.append('transcript_file', params.transcriptFile);
    } else if (params.transcriptText && params.transcriptText.trim()) {
      formData.append('transcript_text', params.transcriptText.trim());
    } else {
      throw new Error('Please provide an audio file, transcript file, or transcript text.');
    }

    if (params.forceReprocess) {
      formData.append('force_reprocess', 'true');
    }

    const res = await fetch(`${API_BASE_URL}/meetings/process`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      let detail = `Server responded with status ${res.status}`;
      try {
        const errorData = await res.json();
        if (errorData.detail) {
          detail = errorData.detail;
        }
      } catch {
        // Fallback to text status
      }
      throw new Error(detail);
    }

    const data: DashboardPayload = await res.json();
    return data;
  },
};
