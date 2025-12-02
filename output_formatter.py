"""
Output formatting module for transcription results
"""

from typing import Dict, List, Optional


class OutputFormatter:
    """
    Formats transcription results into different output formats
    """
    
    @staticmethod
    def format_plain_text(result: Dict) -> str:
        """
        Format as plain text
        
        Args:
            result: Transcription result dictionary
            
        Returns:
            Plain text string
        """
        return result.get("text", "")
    
    @staticmethod
    def format_paragraphs(result: Dict, min_segment_gap: float = 2.0) -> str:
        """
        Format as paragraphs based on segment gaps
        
        Args:
            result: Transcription result dictionary
            min_segment_gap: Minimum gap in seconds to start new paragraph
            
        Returns:
            Paragraph-formatted text
        """
        segments = result.get("segments", [])
        if not segments:
            return result.get("text", "")
        
        paragraphs = []
        current_paragraph = []
        prev_end = 0
        
        for segment in segments:
            start = segment.get("start", 0)
            text = segment.get("text", "").strip()
            
            if not text or len(text) < 2:
                continue
            
            if start - prev_end > min_segment_gap and current_paragraph:
                paragraphs.append(" ".join(current_paragraph))
                current_paragraph = []
            
            current_paragraph.append(text)
            prev_end = segment.get("end", start)
        
        if current_paragraph:
            paragraphs.append(" ".join(current_paragraph))
        
        return "\n\n".join(paragraphs)
    
    @staticmethod
    def format_timestamped(result: Dict, include_speakers: bool = True) -> str:
        """
        Format with timestamps and optional speaker labels
        
        Args:
            result: Transcription result dictionary
            include_speakers: Whether to include speaker labels (Party1, Party2, etc.)
            
        Returns:
            Timestamped text string
        """
        segments = result.get("segments", [])
        if not segments:
            return result.get("text", "")
        
        if include_speakers:
            segments = OutputFormatter._assign_speakers(segments)
        
        lines = []
        for segment in segments:
            start = segment.get("start", 0)
            end = segment.get("end", start)
            text = segment.get("text", "").strip()
            speaker = segment.get("speaker", None)
            
            if text and len(text) > 1:
                start_time = OutputFormatter._format_timestamp(start)
                end_time = OutputFormatter._format_timestamp(end)
                
                if speaker:
                    lines.append(f"[{start_time} - {end_time}] {speaker}: {text}")
                else:
                    lines.append(f"[{start_time} - {end_time}] {text}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _assign_speakers(segments: List[Dict], gap_threshold: float = 3.0) -> List[Dict]:
        """
        Assign speaker labels (Party1, Party2, etc.) based on segment gaps and patterns
        
        Args:
            segments: List of segment dictionaries
            gap_threshold: Minimum gap in seconds to consider a speaker change (increased for better accuracy)
            
        Returns:
            Segments with speaker labels assigned
        """
        if not segments:
            return segments
        
        if len(segments) == 1:
            segment_copy = segments[0].copy()
            segment_copy["speaker"] = "Party1"
            return [segment_copy]
        
        labeled_segments = []
        current_speaker = 1
        prev_end = 0
        prev_speaker = 1
        speaker_changes = 0
        total_gaps = 0
        significant_gaps = 0
        gap_durations = []
        
        for i, segment in enumerate(segments):
            start = segment.get("start", 0)
            end = segment.get("end", start)
            gap = start - prev_end
            
            if i > 0:
                total_gaps += 1
                gap_durations.append(gap)
                if gap > gap_threshold:
                    significant_gaps += 1
            
            segment_copy = segment.copy()
            
            if i == 0:
                segment_copy["speaker"] = f"Party{current_speaker}"
                prev_speaker = current_speaker
            elif gap > gap_threshold:
                if speaker_changes == 0:
                    current_speaker = 2
                    speaker_changes += 1
                else:
                    current_speaker = (prev_speaker % 2) + 1
                
                segment_copy["speaker"] = f"Party{current_speaker}"
                prev_speaker = current_speaker
            else:
                segment_copy["speaker"] = f"Party{prev_speaker}"
            
            labeled_segments.append(segment_copy)
            prev_end = end
        
        unique_speakers = len(set(seg.get("speaker") for seg in labeled_segments))
        
        if unique_speakers == 1:
            return labeled_segments
        
        if total_gaps > 0:
            gap_ratio = significant_gaps / total_gaps
            avg_gap = sum(gap_durations) / len(gap_durations) if gap_durations else 0
            
            if gap_ratio < 0.25 or (speaker_changes < 2 and avg_gap < gap_threshold * 1.5):
                for seg in labeled_segments:
                    seg["speaker"] = "Party1"
                return labeled_segments
        
        return labeled_segments
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """
        Format seconds to HH:MM:SS.mmm
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    @staticmethod
    def format_all(result: Dict, include_timestamps: bool = False) -> str:
        """
        Format with all options
        
        Args:
            result: Transcription result dictionary
            include_timestamps: Whether to include timestamps
            
        Returns:
            Formatted text string
        """
        if include_timestamps:
            return OutputFormatter.format_timestamped(result)
        else:
            return OutputFormatter.format_paragraphs(result)

