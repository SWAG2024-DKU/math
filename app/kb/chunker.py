from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from transformers import AutoTokenizer

from app.schemas.chunk import (
    ChunkCollection,
    ChunkType,
    ConceptChunk,
)


@dataclass
class ChunkSource:
    """DB에서 읽어 온 Concept 데이터임."""

    concept_id: str
    subject_id: str
    chapter_id: str
    concept_name_ko: str
    content_version: int
    content: dict[str, Any]


class ConceptChunker:
    """
    Concept JSONB를 의미 단위 Chunk로 분할함.

    Chunk 크기보다 의미 단위 보존을 우선함.
    """

    # 중간 분할을 허용하지 않는 원자 단위임.
    ATOMIC_CHUNK_TYPES: set[str] = {
        "formula",
        "condition",
        "property",
        "misconception",
    }

    def __init__(
        self,
        model_name: str,
        max_tokens: int = 420,
    ) -> None:
        if max_tokens < 50:
            raise ValueError(
                "max_tokens는 50 이상이어야 함."
            )

        self.model_name = model_name
        self.max_tokens = max_tokens

        print(
            f"Tokenizer 불러오는 중: {model_name}"
        )

        self.tokenizer = (
            AutoTokenizer.from_pretrained(
                model_name
            )
        )

    def count_tokens(
        self,
        text: str,
    ) -> int:
        """Embedding 모델 기준 토큰 수를 계산함."""

        encoded = self.tokenizer(
            text,
            add_special_tokens=True,
            truncation=False,
        )

        return len(encoded["input_ids"])

    @staticmethod
    def calculate_hash(
        text: str,
    ) -> str:
        """Chunk 텍스트의 SHA-256 해시를 생성함."""

        return hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def format_value(
        value: Any,
    ) -> str:
        """JSON 값을 사람이 읽을 수 있는 문자열로 변환함."""

        if value is None:
            return "없음"

        if isinstance(value, bool):
            return "참" if value else "거짓"

        if isinstance(value, list):
            return ", ".join(
                ConceptChunker.format_value(item)
                for item in value
            )

        if isinstance(value, dict):
            return json.dumps(
                value,
                ensure_ascii=False,
            )

        return str(value)

    def build_common_header(
        self,
        source: ChunkSource,
        chunk_type: ChunkType,
    ) -> str:
        """모든 Chunk에 공통 문맥 정보를 추가함."""

        subject = source.content.get(
            "subject",
            {},
        )

        unit = source.content.get(
            "unit",
            {},
        )

        subject_name = subject.get(
            "name_ko",
            source.subject_id,
        )

        unit_name = unit.get(
            "name_ko",
            source.chapter_id,
        )

        type_names = {
            "definition": "정의 및 개요",
            "formula": "핵심 공식",
            "condition": "적용 조건",
            "property": "주요 성질",
            "learning": "선수 및 학습 관계",
            "misconception": "오개념 및 피드백",
            "generation": "문제 생성 정보",
        }

        return "\n".join(
            [
                f"과목: {subject_name}",
                f"단원: {unit_name}",
                f"개념: {source.concept_name_ko}",
                f"개념 ID: {source.concept_id}",
                f"정보 유형: {type_names[chunk_type]}",
            ]
        )

    @staticmethod
    def build_content_text(
        header: str,
        heading: str,
        body: str,
    ) -> str:
        """Chunk의 최종 텍스트를 구성함."""

        return (
            f"{header}\n\n"
            f"{heading}\n"
            f"{body.strip()}"
        )

    def fits_limit(
        self,
        header: str,
        heading: str,
        body: str,
    ) -> bool:
        """본문을 포함한 전체 Chunk가 상한 이하인지 확인함."""

        content_text = self.build_content_text(
            header=header,
            heading=heading,
            body=body,
        )

        return (
            self.count_tokens(content_text)
            <= self.max_tokens
        )

    @staticmethod
    def split_sentences(
        text: str,
    ) -> list[str]:
        """
        텍스트를 완성된 문장 경계에서 분리함.

        마침표, 물음표, 느낌표 뒤의 공백을 기준으로 함.
        """

        sentences = re.split(
            r"(?<=[.!?。！？])\s+",
            text.strip(),
        )

        return [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

    def create_semantic_units(
        self,
        text: str,
        header: str,
        heading: str,
    ) -> list[str]:
        """
        긴 설명 텍스트를 의미 경계에서만 분리함.

        우선순위:
        1. 문단
        2. 줄
        3. 문장

        단일 문장이 상한을 초과하면 강제 절단하지 않음.
        """

        paragraphs = [
            paragraph.strip()
            for paragraph in re.split(
                r"\n\s*\n",
                text,
            )
            if paragraph.strip()
        ]

        if not paragraphs:
            paragraphs = [text.strip()]

        semantic_units: list[str] = []

        for paragraph in paragraphs:
            # 문단이 그대로 들어가면 유지함.
            if self.fits_limit(
                header=header,
                heading=heading,
                body=paragraph,
            ):
                semantic_units.append(paragraph)
                continue

            # 문단이 길면 줄 단위로 확인함.
            lines = [
                line.strip()
                for line in paragraph.splitlines()
                if line.strip()
            ]

            if len(lines) > 1:
                for line in lines:
                    if self.fits_limit(
                        header=header,
                        heading=heading,
                        body=line,
                    ):
                        semantic_units.append(line)
                        continue

                    sentences = self.split_sentences(
                        line
                    )

                    if len(sentences) <= 1:
                        token_count = self.count_tokens(
                            self.build_content_text(
                                header=header,
                                heading=heading,
                                body=line,
                            )
                        )

                        raise ValueError(
                            "\n".join(
                                [
                                    "단일 의미 단위가 최대 토큰 수를 초과함.",
                                    "문장이나 수식을 강제로 절단하지 않음.",
                                    (
                                        f"토큰 수: {token_count} / "
                                        f"상한: {self.max_tokens}"
                                    ),
                                    f"내용: {line[:300]}",
                                ]
                            )
                        )

                    for sentence in sentences:
                        if not self.fits_limit(
                            header=header,
                            heading=heading,
                            body=sentence,
                        ):
                            token_count = (
                                self.count_tokens(
                                    self.build_content_text(
                                        header=header,
                                        heading=heading,
                                        body=sentence,
                                    )
                                )
                            )

                            raise ValueError(
                                "\n".join(
                                    [
                                        (
                                            "단일 문장이 최대 토큰 수를 "
                                            "초과함."
                                        ),
                                        (
                                            "문장 중간 자동 절단을 "
                                            "수행하지 않음."
                                        ),
                                        (
                                            f"토큰 수: {token_count} / "
                                            f"상한: {self.max_tokens}"
                                        ),
                                        (
                                            f"내용: "
                                            f"{sentence[:300]}"
                                        ),
                                    ]
                                )
                            )

                        semantic_units.append(
                            sentence
                        )

                continue

            # 줄 구분이 없으면 문장 단위로 분리함.
            sentences = self.split_sentences(
                paragraph
            )

            if len(sentences) <= 1:
                token_count = self.count_tokens(
                    self.build_content_text(
                        header=header,
                        heading=heading,
                        body=paragraph,
                    )
                )

                raise ValueError(
                    "\n".join(
                        [
                            "분할 가능한 문장 경계를 찾지 못함.",
                            (
                                "문장 또는 수식을 강제로 "
                                "절단하지 않음."
                            ),
                            (
                                f"토큰 수: {token_count} / "
                                f"상한: {self.max_tokens}"
                            ),
                            f"내용: {paragraph[:300]}",
                        ]
                    )
                )

            for sentence in sentences:
                if not self.fits_limit(
                    header=header,
                    heading=heading,
                    body=sentence,
                ):
                    token_count = self.count_tokens(
                        self.build_content_text(
                            header=header,
                            heading=heading,
                            body=sentence,
                        )
                    )

                    raise ValueError(
                        "\n".join(
                            [
                                (
                                    "단일 문장이 최대 토큰 수를 "
                                    "초과함."
                                ),
                                (
                                    "문장 중간 자동 절단을 "
                                    "수행하지 않음."
                                ),
                                (
                                    f"토큰 수: {token_count} / "
                                    f"상한: {self.max_tokens}"
                                ),
                                f"내용: {sentence[:300]}",
                            ]
                        )
                    )

                semantic_units.append(sentence)

        return semantic_units

    def pack_semantic_units(
        self,
        units: list[str],
        header: str,
        heading: str,
    ) -> list[str]:
        """
        의미 단위를 최대 토큰 범위 안에서 묶음.

        개별 의미 단위의 중간은 자르지 않음.
        """

        results: list[str] = []
        current_units: list[str] = []

        for unit in units:
            candidate_units = [
                *current_units,
                unit,
            ]

            candidate_body = "\n\n".join(
                candidate_units
            )

            if self.fits_limit(
                header=header,
                heading=heading,
                body=candidate_body,
            ):
                current_units.append(unit)
                continue

            if current_units:
                results.append(
                    "\n\n".join(current_units)
                )

                current_units = []

            if not self.fits_limit(
                header=header,
                heading=heading,
                body=unit,
            ):
                token_count = self.count_tokens(
                    self.build_content_text(
                        header=header,
                        heading=heading,
                        body=unit,
                    )
                )

                raise ValueError(
                    "\n".join(
                        [
                            (
                                "의미 단위 하나가 최대 토큰 수를 "
                                "초과함."
                            ),
                            (
                                f"토큰 수: {token_count} / "
                                f"상한: {self.max_tokens}"
                            ),
                            f"내용: {unit[:300]}",
                        ]
                    )
                )

            current_units.append(unit)

        if current_units:
            results.append(
                "\n\n".join(current_units)
            )

        return results

    def split_long_text(
        self,
        text: str,
        header: str,
        heading: str,
    ) -> list[str]:
        """
        긴 설명 텍스트를 문단·줄·문장 경계에서만 분할함.

        토큰 위치 기준 강제 절단은 수행하지 않음.
        """

        if self.fits_limit(
            header=header,
            heading=heading,
            body=text,
        ):
            return [text]

        semantic_units = self.create_semantic_units(
            text=text,
            header=header,
            heading=heading,
        )

        return self.pack_semantic_units(
            units=semantic_units,
            header=header,
            heading=heading,
        )

    def pack_items(
        self,
        source: ChunkSource,
        chunk_type: ChunkType,
        heading: str,
        items: list[str],
    ) -> list[
        tuple[str, str, dict[str, Any]]
    ]:
        """
        여러 의미 항목을 최대 토큰 이하로 묶음.

        공식·조건·성질·오개념은 원자 단위로 보존함.
        """

        if not items:
            return []

        header = self.build_common_header(
            source=source,
            chunk_type=chunk_type,
        )

        packed_chunks: list[
            tuple[str, str, dict[str, Any]]
        ] = []

        current_items: list[str] = []

        def flush_current_items() -> None:
            nonlocal current_items

            if not current_items:
                return

            body = "\n\n".join(
                current_items
            )

            content_text = self.build_content_text(
                header=header,
                heading=heading,
                body=body,
            )

            packed_chunks.append(
                (
                    heading,
                    content_text,
                    {
                        "item_count": len(
                            current_items
                        ),
                        "split_strategy": (
                            "semantic_item_boundary"
                        ),
                    },
                )
            )

            current_items = []

        for item_number, item in enumerate(
            items,
            start=1,
        ):
            candidate_items = [
                *current_items,
                item,
            ]

            candidate_body = "\n\n".join(
                candidate_items
            )

            if self.fits_limit(
                header=header,
                heading=heading,
                body=candidate_body,
            ):
                current_items.append(item)
                continue

            # 기존 항목을 먼저 하나의 Chunk로 확정함.
            flush_current_items()

            # 항목 하나가 그대로 들어가는지 확인함.
            if self.fits_limit(
                header=header,
                heading=heading,
                body=item,
            ):
                current_items.append(item)
                continue

            # 공식, 조건 등의 원자 단위는 절대 나누지 않음.
            if (
                chunk_type
                in self.ATOMIC_CHUNK_TYPES
            ):
                token_count = self.count_tokens(
                    self.build_content_text(
                        header=header,
                        heading=heading,
                        body=item,
                    )
                )

                raise ValueError(
                    "\n".join(
                        [
                            (
                                "원자 단위 Chunk가 최대 토큰 수를 "
                                "초과함."
                            ),
                            (
                                "공식·조건·성질·오개념은 "
                                "중간 분할하지 않음."
                            ),
                            (
                                f"Concept ID: "
                                f"{source.concept_id}"
                            ),
                            f"Chunk 유형: {chunk_type}",
                            f"항목 번호: {item_number}",
                            (
                                f"토큰 수: {token_count} / "
                                f"상한: {self.max_tokens}"
                            ),
                            f"내용: {item[:300]}",
                        ]
                    )
                )

            # 정의·학습·생성 정보만 문장 경계 분할을 허용함.
            split_items = self.split_long_text(
                text=item,
                header=header,
                heading=heading,
            )

            for split_number, split_item in enumerate(
                split_items,
                start=1,
            ):
                split_content = (
                    self.build_content_text(
                        header=header,
                        heading=heading,
                        body=split_item,
                    )
                )

                packed_chunks.append(
                    (
                        heading,
                        split_content,
                        {
                            "item_count": 1,
                            "semantic_split": True,
                            "source_item_number": (
                                item_number
                            ),
                            "split_part_number": (
                                split_number
                            ),
                            "split_strategy": (
                                "paragraph_line_sentence"
                            ),
                        },
                    )
                )

        flush_current_items()

        return packed_chunks

    def build_definition_items(
        self,
        source: ChunkSource,
    ) -> list[str]:
        """정의 및 검색 태그 항목을 생성함."""

        definition = source.content.get(
            "definition"
        )

        if not definition:
            return []

        tags = source.content.get(
            "tags",
            [],
        )

        parts = [
            f"정의: {definition}"
        ]

        if tags:
            parts.append(
                "검색 태그: "
                + ", ".join(tags)
            )

        return ["\n".join(parts)]

    def build_formula_items(
        self,
        source: ChunkSource,
    ) -> list[str]:
        """공식별 원자 항목을 생성함."""

        formulas = source.content.get(
            "formulas",
            [],
        )

        results: list[str] = []

        for formula in formulas:
            lines = [
                (
                    f"공식명: "
                    f"{formula.get('name_ko', '')}"
                ),
                (
                    f"공식 ID: "
                    f"{formula.get('formula_id', '')}"
                ),
                (
                    f"역할: "
                    f"{formula.get('role', '')}"
                ),
                (
                    f"LaTeX: "
                    f"{formula.get('latex', '')}"
                ),
            ]

            cas = formula.get("cas")

            if cas:
                lines.append(
                    f"CAS 표현: {cas}"
                )

            results.append(
                "\n".join(lines)
            )

        return results

    def build_condition_items(
        self,
        source: ChunkSource,
    ) -> list[str]:
        """적용 조건별 원자 항목을 생성함."""

        conditions = source.content.get(
            "application_conditions",
            [],
        )

        results: list[str] = []

        for condition in conditions:
            lines = [
                (
                    f"조건 ID: "
                    f"{condition.get('condition_id', '')}"
                ),
                (
                    f"설명: "
                    f"{condition.get('description', '')}"
                ),
            ]

            rule = condition.get("rule")

            if isinstance(rule, dict):
                lines.append(
                    "검증 규칙: "
                    f"{rule.get('property', '')} "
                    f"{rule.get('operator', '')} "
                    f"{self.format_value(rule.get('value'))}"
                )

            results.append(
                "\n".join(lines)
            )

        return results

    def build_property_items(
        self,
        source: ChunkSource,
    ) -> list[str]:
        """주요 성질별 원자 항목을 생성함."""

        properties = source.content.get(
            "properties",
            [],
        )

        return [
            "\n".join(
                [
                    (
                        f"성질 ID: "
                        f"{item.get('property_id', '')}"
                    ),
                    (
                        f"설명: "
                        f"{item.get('description', '')}"
                    ),
                ]
            )
            for item in properties
        ]

    def build_learning_items(
        self,
        source: ChunkSource,
    ) -> list[str]:
        """선수 개념·관련 개념·학습 목표를 생성함."""

        results: list[str] = []

        prerequisites = source.content.get(
            "prerequisites",
            [],
        )

        if prerequisites:
            lines = ["선수 개념:"]

            for item in prerequisites:
                lines.append(
                    "- "
                    f"{item.get('name_ko', '')} "
                    f"({item.get('concept_id', '')}, "
                    f"중요도: "
                    f"{item.get('importance', '')})"
                )

            results.append(
                "\n".join(lines)
            )

        related = source.content.get(
            "related_concepts",
            [],
        )

        if related:
            results.append(
                "관련 개념:\n- "
                + "\n- ".join(related)
            )

        objectives = source.content.get(
            "learning_objectives",
            [],
        )

        for objective in objectives:
            results.append(
                "\n".join(
                    [
                        (
                            f"학습 목표 ID: "
                            f"{objective.get('objective_id', '')}"
                        ),
                        (
                            f"행동 동사: "
                            f"{objective.get('verb', '')}"
                        ),
                        (
                            f"목표: "
                            f"{objective.get('description', '')}"
                        ),
                    ]
                )
            )

        return results

    def build_misconception_items(
        self,
        source: ChunkSource,
    ) -> list[str]:
        """오개념과 피드백을 하나의 원자 항목으로 생성함."""

        misconceptions = source.content.get(
            "misconceptions",
            [],
        )

        results: list[str] = []

        for item in misconceptions:
            results.append(
                "\n".join(
                    [
                        (
                            f"오개념: "
                            f"{item.get('title', '')}"
                        ),
                        (
                            f"오개념 ID: "
                            f"{item.get('misconception_id', '')}"
                        ),
                        (
                            f"설명: "
                            f"{item.get('description', '')}"
                        ),
                        (
                            f"진단 태그: "
                            f"{item.get('diagnosis_tag', '')}"
                        ),
                        (
                            f"피드백: "
                            f"{item.get('feedback', '')}"
                        ),
                    ]
                )
            )

        return results

    def build_generation_items(
        self,
        source: ChunkSource,
    ) -> list[str]:
        """문제 생성 프로필 항목을 생성함."""

        profile = source.content.get(
            "generation_profile"
        )

        if not isinstance(profile, dict):
            return []

        difficulty = profile.get(
            "difficulty_range",
            {},
        )

        lines = [
            (
                "문제 생성 활성화: "
                f"{self.format_value(profile.get('enabled'))}"
            ),
            (
                "지원 문제 유형: "
                + ", ".join(
                    profile.get(
                        "supported_problem_types",
                        [],
                    )
                )
            ),
            (
                "지원 정답 유형: "
                + ", ".join(
                    profile.get(
                        "supported_answer_types",
                        [],
                    )
                )
            ),
            (
                "난이도 범위: "
                f"{difficulty.get('min', '')}"
                " ~ "
                f"{difficulty.get('max', '')}"
            ),
            (
                "권장 검증기: "
                + ", ".join(
                    profile.get(
                        "recommended_validators",
                        [],
                    )
                )
            ),
        ]

        generation_notes = profile.get(
            "generation_notes"
        )

        if generation_notes:
            lines.append(
                f"생성 참고사항: {generation_notes}"
            )

        return [
            "\n".join(lines)
        ]

    def create_chunks(
        self,
        source: ChunkSource,
    ) -> ChunkCollection:
        """Concept 하나에서 전체 Chunk를 생성함."""

        section_specs: list[
            tuple[
                ChunkType,
                str,
                list[str],
            ]
        ] = [
            (
                "definition",
                "개념 정의",
                self.build_definition_items(
                    source
                ),
            ),
            (
                "formula",
                "핵심 공식",
                self.build_formula_items(
                    source
                ),
            ),
            (
                "condition",
                "공식 및 개념의 적용 조건",
                self.build_condition_items(
                    source
                ),
            ),
            (
                "property",
                "주요 성질",
                self.build_property_items(
                    source
                ),
            ),
            (
                "learning",
                "선수 개념·관련 개념·학습 목표",
                self.build_learning_items(
                    source
                ),
            ),
            (
                "misconception",
                "자주 발생하는 오개념과 피드백",
                self.build_misconception_items(
                    source
                ),
            ),
            (
                "generation",
                "문제 생성 프로필",
                self.build_generation_items(
                    source
                ),
            ),
        ]

        chunk_drafts: list[
            tuple[
                ChunkType,
                str,
                str,
                dict[str, Any],
            ]
        ] = []

        for (
            chunk_type,
            heading,
            items,
        ) in section_specs:
            packed = self.pack_items(
                source=source,
                chunk_type=chunk_type,
                heading=heading,
                items=items,
            )

            for (
                packed_heading,
                content_text,
                metadata,
            ) in packed:
                chunk_drafts.append(
                    (
                        chunk_type,
                        packed_heading,
                        content_text,
                        metadata,
                    )
                )

        chunks: list[ConceptChunk] = []

        for chunk_index, (
            chunk_type,
            heading,
            content_text,
            metadata,
        ) in enumerate(chunk_drafts):
            token_count = self.count_tokens(
                content_text
            )

            if token_count > self.max_tokens:
                raise RuntimeError(
                    "\n".join(
                        [
                            (
                                "생성된 Chunk가 최대 토큰 수를 "
                                "초과함."
                            ),
                            (
                                f"Concept ID: "
                                f"{source.concept_id}"
                            ),
                            f"Chunk index: {chunk_index}",
                            f"Chunk 유형: {chunk_type}",
                            (
                                f"토큰 수: {token_count} / "
                                f"상한: {self.max_tokens}"
                            ),
                        ]
                    )
                )

            chunks.append(
                ConceptChunk(
                    concept_id=source.concept_id,
                    subject_id=source.subject_id,
                    chapter_id=source.chapter_id,
                    concept_name_ko=(
                        source.concept_name_ko
                    ),
                    chunk_index=chunk_index,
                    chunk_type=chunk_type,
                    heading=heading,
                    content_text=content_text,
                    token_count=token_count,
                    content_hash=(
                        self.calculate_hash(
                            content_text
                        )
                    ),
                    source_content_version=(
                        source.content_version
                    ),
                    metadata={
                        **metadata,
                        "embedding_model": (
                            self.model_name
                        ),
                        "max_tokens": (
                            self.max_tokens
                        ),
                    },
                )
            )

        if not chunks:
            raise ValueError(
                f"Chunk가 생성되지 않음: "
                f"{source.concept_id}"
            )

        return ChunkCollection(
            concept_id=source.concept_id,
            subject_id=source.subject_id,
            chapter_id=source.chapter_id,
            concept_name_ko=(
                source.concept_name_ko
            ),
            embedding_model=self.model_name,
            max_tokens=self.max_tokens,
            chunks=chunks,
        )